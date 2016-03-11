from __future__ import division
import argparse
import psycopg2, psycopg2.extras
import math
import sys
from decimal import Decimal

def make_indexdef_concurrent(indexdef):
    if indexdef.startswith("CREATE INDEX "):
        indexdef = indexdef.replace("CREATE INDEX ", "CREATE INDEX CONCURRENTLY ", 1)
    elif indexdef.startswith("CREATE UNIQUE INDEX "):
        indexdef = indexdef.replace("CREATE UNQUE INDEX ", "CREATE UNQUE INDEX CONCURRENTLY ", 1)
    else:
        raise ValueError("Unknown index creation: {}".format(indexdef))

    return indexdef

def indexsizes(cursor):
    sql = """SELECT                       
          current_database(), schemaname, tablename, reltuples::bigint, relpages::bigint, otta,
          ROUND(CASE WHEN otta=0 THEN 0.0 ELSE sml.relpages/otta::numeric END,1) AS tbloat,
          CASE WHEN relpages < otta THEN 0 ELSE bs*(sml.relpages-otta)::bigint END AS wastedbytes,
          iname, ituples::bigint, ipages::bigint, iotta,
          ROUND(CASE WHEN iotta=0 OR ipages=0 THEN 0.0 ELSE ipages/iotta::numeric END,1) AS ibloat,
          CASE WHEN ipages < iotta THEN 0 ELSE bs*(ipages-iotta) END AS wastedibytes,
          indisprimary,
          indexdef
        FROM (
          SELECT
            rs.schemaname, rs.tablename, cc.reltuples, cc.relpages, bs, indisprimary, indexdef,
            CEIL((cc.reltuples*((datahdr+ma-
              (CASE WHEN datahdr%ma=0 THEN ma ELSE datahdr%ma END))+nullhdr2+4))/(bs-20::float)) AS otta,
            COALESCE(c2.relname,'?') AS iname, COALESCE(c2.reltuples,0) AS ituples, COALESCE(c2.relpages,0) AS ipages,
            COALESCE(CEIL((c2.reltuples*(datahdr-12))/(bs-20::float)),0) AS iotta -- very rough approximation, assumes all cols
          FROM (
            SELECT
              ma,bs,schemaname,tablename,
              (datawidth+(hdr+ma-(case when hdr%ma=0 THEN ma ELSE hdr%ma END)))::numeric AS datahdr,
              (maxfracsum*(nullhdr+ma-(case when nullhdr%ma=0 THEN ma ELSE nullhdr%ma END))) AS nullhdr2
            FROM (
              SELECT
                schemaname, tablename, hdr, ma, bs,
                SUM((1-null_frac)*avg_width) AS datawidth,
                MAX(null_frac) AS maxfracsum,
                hdr+(
                  SELECT 1+count(*)/8
                  FROM pg_stats s2
                  WHERE null_frac<>0 AND s2.schemaname = s.schemaname AND s2.tablename = s.tablename
                ) AS nullhdr
              FROM pg_stats s, (
                SELECT
                  (SELECT current_setting('block_size')::numeric) AS bs,
                  CASE WHEN substring(v,12,3) IN ('8.0','8.1','8.2') THEN 27 ELSE 23 END AS hdr,
                  CASE WHEN v ~ 'mingw32' THEN 8 ELSE 4 END AS ma
                FROM (SELECT version() AS v) AS foo
              ) AS constants
              GROUP BY 1,2,3,4,5
            ) AS foo
          ) AS rs
          JOIN pg_class cc ON cc.relname = rs.tablename
          JOIN pg_namespace nn ON cc.relnamespace = nn.oid AND nn.nspname = rs.schemaname AND nn.nspname <> 'information_schema'
          LEFT JOIN pg_index i ON indrelid = cc.oid
          LEFT JOIN pg_class c2 ON c2.oid = i.indexrelid
          LEFT JOIN pg_indexes on pg_indexes.indexname = c2.relname
        ) AS sml
        ORDER BY wastedbytes DESC;"""

    cursor.execute(sql)

    #raw_results = cursor.fetchall()

    objs = {}
    for row in cursor.fetchall():
        if row['indexdef']:
            objs["{}.{}".format(row['schemaname'], row['iname'])] = {
                'schemaname': row['schemaname'],
                'iname': row['iname'],
                'name': row['iname'],
                'size': row['ipages'] * 8192,
                'type': 'index',
                'table': row['tablename'],
                'primary': row['indisprimary'],
                'def': row['indexdef'],
                'wasted': row['wastedibytes'],
                'indexdef': make_indexdef_concurrent(row['indexdef']),
                }



    objs = objs.values()
    objs.sort(key=lambda t: t['wasted'], reverse=True)

    # TODO should probably do this in the SQL query above.
    objs = [o for o in objs if o['schemaname'] != 'pg_catalog']

    return objs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', type=str, required=True, help="PostgreSQL database name")
    args = parser.parse_args()

    connect_args = {}
    if args.database is not None:
        connect_args['database'] = args.database



    conn = psycopg2.connect(**connect_args)

    # Need this transaction isolation level for CREATE INDEX CONCURRENTLY
    # cf. http://stackoverflow.com/questions/3413646/postgres-raises-a-active-sql-transaction-errcode-25001
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    objs = indexsizes(cursor)

    total_used = sum(Decimal(x['size']) for x in objs)
    total_wasted = sum(Decimal(x['wasted']) for x in objs)
    print "DB used:   {:>20,}\nDB wasted: {:>20,}".format(total_used, total_wasted)

    while True:
        print "\n\nStart of loop\n"

        for obj in objs:
            if obj['wasted'] == 0:
                print "Skipping Index {name:>50} size {size:>15,} wasted {wasted:>15,}".format(**obj)
                continue
            if ' UNIQUE ' in obj['indexdef'].upper():
                # FIXME Better unique index detection
                # FIXME Don't skip unique indexes, instead figure out how to
                # recreate the unique contraint, like we do with PRIMARY KEYS
                print "Skipping Index {name:>50} size {size:>15,} wasted {wasted:>15,} because it has a unique contrainst".format(**obj)
                continue

            print "Reindexing {name:>50} size {size:>15,} wasted {wasted:>15,}".format(**obj)

            cursor.execute("ALTER INDEX {t} RENAME TO {t}_old;".format(t=obj['name']))
            cursor.execute(obj['indexdef'])
            cursor.execute("ANALYSE {t};".format(t=obj['name']))

            if obj['primary']:
                cursor.execute("ALTER TABLE {table} DROP CONSTRAINT {t}_old, ADD CONSTRAINT {t} PRIMARY KEY USING INDEX {t};".format(t=obj['name'], table=obj['table']))


            cursor.execute("DROP INDEX {t}_old;".format(t=obj['name']))

        # TODO in future look at disk space and keep going
        break


    

if __name__ == '__main__':
    main()
