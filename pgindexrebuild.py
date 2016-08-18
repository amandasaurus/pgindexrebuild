"""
Reindexes indexes to save space, but does it in a non-locking manner.

This recovers space from index bloat.
"""
from __future__ import division
import argparse
import psycopg2
import psycopg2.extras
import math
import sys
from decimal import Decimal
import logging, logging.handlers
import humanfriendly
import os
import fcntl

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def version():
    """Returns the version installed via pip"""
    import pkg_resources
    return pkg_resources.require("pgindexrebuild")[0].version

def make_indexdef_concurrent(indexdef):
    """Turn an index creation statement into a concurrent index creationstatement."""
    if indexdef.startswith("CREATE INDEX "):
        indexdef = indexdef.replace("CREATE INDEX ", "CREATE INDEX CONCURRENTLY ", 1)
    elif indexdef.startswith("CREATE UNIQUE INDEX "):
        indexdef = indexdef.replace("CREATE UNQUE INDEX ", "CREATE UNQUE INDEX CONCURRENTLY ", 1)
    else:
        raise ValueError("Unknown index creation: {}".format(indexdef))

    return indexdef


def index_size(cursor, iname):
    cursor.execute("select pg_relation_size(pg_class.oid) FROM pg_class WHERE relname = %s;", (iname,))
    size = cursor.fetchone()[0]
    return size


def does_index_exist(cursor, iname):
    cursor.execute("select 1 from pg_indexes where schemaname = 'public' and indexname = %s limit 1;", (iname,))
    result = cursor.fetchone()
    return result == [1]


def format_size(b):
    b = int(b)
    if b == 0:
        return "0 bytes"
    else:
        return "{} ({:,} bytes)".format(humanfriendly.format_size(b), b)

def indexsizes(cursor):
    """Return the sizes of all the indexes."""
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
    objs.sort(key=lambda t: t['wasted'])

    # TODO should probably do this in the SQL query above.
    objs = [o for o in objs if o['schemaname'] == 'public' and o['wasted'] > 0]

    return objs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', type=str, help="PostgreSQL database name")
    parser.add_argument('-a', '--all-databases', action="store_true", help="Run on all databases")
    parser.add_argument('-U', '--user', type=str, required=False, help="PostgreSQL database user")
    parser.add_argument('-n', '--dry-run', action="store_true", help="Dry run, don't do any processing")

    parser.add_argument('--min-bloat', type=humanfriendly.parse_size, required=False, default=8192, help="Don't reindex indexes with less than this much bloat (default: 8KB)")

    parser.add_argument('--always-drop-first', '--super-slim-mode', action="store_true", help="Rather than keep the old index around, this drops the index first, and then rebuilds a new one. This is useful if the disk is too full for the intermediate index. THIS WILL DEGRADE DATABASE PERFORMANCE!")

    parser.add_argument('--log-syslog', action="store_true", dest="log_syslog", help="Log to syslog (default)", default=True)
    parser.add_argument('--no-log-syslog', action="store_false", dest="log_syslog", help="Don't log to syslog")

    parser.add_argument('--log-stdout', action="store_true", dest="log_stdout", help="Log to stdout (default)", default=True)
    parser.add_argument('--no-log-stdout', action="store_false", dest="log_stdout", help="Don't log to stdout")
    parser.add_argument('-q', "--quiet", action="store_false", dest="log_stdout", help="Same as --no-log-stdout. Won't print to terminal.")

    parser.add_argument("--lock-file", required=False, metavar="PATH", help="Use a PATH as a lock file using flock/fncntl. If a lock cannot be acquired immediatly, programme halts without changing anything.")

    args = parser.parse_args()

    if args.log_stdout:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
        logger.addHandler(handler)

    if args.log_syslog:
        handler = logging.handlers.SysLogHandler("/dev/log")
        handler.setLevel(logging.DEBUG)
        # Unix convention of the PID & process at the start. syslog already has datetime so don't need to include that
        handler.setFormatter(logging.Formatter('pgindexrebuild[{pid}]: %(levelname)s: %(message)s'.format(pid=os.getpid())))
        logger.addHandler(handler)

    # Ensure we always have at least one handler. Otherwise with --no-log-syslog --no-log-stdout there'd be an error
    logger.addHandler(logging.NullHandler())

    connect_args = {}
    if args.database is not None:
        connect_args['database'] = args.database
    if args.user is not None:
        connect_args['user'] = args.user

    logger.info("Starting pgindexrebuild {}".format(version()))

    # Lock?
    # We don't explicitly close the file handle, that'll be done automatically
    # when the programme ends. Which will release the lock
    lock_file = None
    if args.lock_file:
        try:
            lock_file = open(args.lock_file, 'w')
        except IOError as ex:
            logger.error("Could not open lock file {}. Do you have permission? Cannot get lock. Exiting without doing anything.".format(args.lock_file))
            return

        try:
            # Try to get a lock on the file
            # LOCK_EX because we want an exclusive lock, so no-one else can get this
            # LOCK_NB = non-blocking. If you cannot get a lock straight away,
            # throw an error. Otherwise it will wait (block) until it can get a
            # lock
            fcntl.flock(lock_file, fcntl.LOCK_EX|fcntl.LOCK_NB)
            logger.info("Acquired a lock on {}. Other instances of pgindexrebuild will not run.".format(args.lock_file))
        except IOError:
            # File is already locked!
            logger.info("Another instance of pgindexrebuild is running! Could not get a lock on {}. Exiting.".format(args.lock_file))
            return

    conn = None
    databases = []
    if args.all_databases:
        # work on all database

        # psycopg2 requires that we have at least one argument in the
        # connect_args, so set this to a database that we know works
        connect_args['database'] = 'postgres'

        conn = psycopg2.connect(**connect_args)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        # TODO Find out sizes (like \l+) and sort by that. Work on smallest dbs first
        cursor.execute("SELECT datname from pg_database where datistemplate = false order by datname")
        databases = [row[0] for row in cursor.fetchall()]
        conn.close()
        logger.info("Running on all databases: Found {} database: {}".format(len(databases), ", ".join(databases)))
    elif args.database is not None:
        logger.info("Only operating on one database: {}".format(args.database))
        databases = [args.database]
    else:
        # TODO shouldn't this use the user's one?
        logger.error("What do you want to do? You must provide either a database name (with -d) or --all-databases to work on all databases")
        return

    total_savings = 0

    always_drop_first = args.always_drop_first
    if always_drop_first:
        logger.info("Running in super slim mode. Indexes will be dropped and database performance will degrade")
    else:
        logger.info("Running in normal mode. Old, bloated index will be kept around.")

    if args.dry_run:
        logger.info("Running in dry-run mode, no changes will be made")

    for database in databases:
        if conn:
            conn.close()
        connect_args['database'] = database
        try:
            conn = psycopg2.connect(**connect_args)
        except psycopg2.OperationalError as ex:
            logger.error("Unable to connect to database {}. Error: {!r}".format(database, ex))
            continue

        logger.info("Connected to database {}{}".format(database, (" as user {}".format(args.user) if args.user else " as unspecified user")))

        # Need this transaction isolation level for CREATE INDEX CONCURRENTLY
        # cf. http://stackoverflow.com/questions/3413646/postgres-raises-a-active-sql-transaction-errcode-25001
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        objs = indexsizes(cursor)

        if len(objs) == 0:
            logger.info("No indexes found for database {}. Either you have no permission to read them, or there is no index bloat in this database.".format(database))
            continue

        total_used = sum(Decimal(x['size']) for x in objs)
        total_wasted = sum(Decimal(x['wasted']) for x in objs)
        percent_wasted = "N/A" if total_used == 0 else "{:.0%}".format(float(total_wasted)/float(total_used))
        logger.info("DB {}: Used space: {} Wasted space: {} {} wasted space".format(database, format_size(total_used), format_size(total_wasted), percent_wasted))


        min_bloat = args.min_bloat
        logger.info("Ignoring all tables with a bloat less than {}".format(format_size(min_bloat)))

        total_savings_this_database = 0

        for obj in objs:
            if obj['wasted'] == 0:
                logger.info("Skipping Index {name} size {size} wasted {wasted}".format(name=obj['name'], size=format_size(obj['size']), wasted=format_size(obj['wasted'])))
                continue
            if obj['wasted'] <= min_bloat:
                logger.info("Skipping Index {name} size {size} wasted {wasted} which is less than min bloat {min_bloat}".format(name=obj['name'], size=format_size(obj['size']), wasted=format_size(obj['wasted']), min_bloat=format_size(min_bloat)))
                continue

            if ' UNIQUE ' in obj['indexdef'].upper():
                # FIXME Better unique index detection
                # FIXME Don't skip unique indexes, instead figure out how to
                # recreate the unique contraint, like we do with PRIMARY KEYS
                logger.info("Skipping Index {} size {} wasted {} because it has a unique constraint".format(obj['name'], format_size(obj['size']), format_size(obj['wasted'])))
                continue

            oldsize = index_size(cursor, obj['name'])
            logger.info("Reindexing {} size {} wasted {} {:.0%}".format(obj['name'], format_size(obj['size']), format_size(obj['wasted']), float(obj['wasted']) / obj['size']))

            if not args.dry_run:
                old_index_name = "{t}_old".format(t=obj['name'])

                if does_index_exist(cursor, old_index_name):
                    logger.info("The index {old} already exists. This can happen when a previous run of this has been interrupted. You can delete this old index with:  DROP INDEX {old};  Processing will continue with the rest of the indexes".format(old=old_index_name))
                    continue

                if not always_drop_first:
                    # Move old index out of the way
                    logger.debug("Renamed index {t} to {t}_old".format(t=obj['name']))
                    cursor.execute("ALTER INDEX {t} RENAME TO {old};".format(t=obj['name'], old=old_index_name))
                else:
                    # Super slim mode, delete it
                    logger.debug("Dropped index {t}".format(t=obj['name']))
                    cursor.execute("DROP INDEX {t};".format(t=obj['name']))

                # (Re-)Create the new index
                logger.debug("Index creation SQL: {}".format(obj['indexdef']))
                try:
                    cursor.execute(obj['indexdef'])
                except psycopg2.OperationalError as e:
                    if e.pgerror.startswith('ERROR:  could not extend file') and e.pgerror.endswith("No space left on device\nHINT:  Check free disk space.\n"):
                        # Disk is full
                        logger.error("Disk is full! Cannot proceed. Attempting to roll back")
                        # drop newly created, and invalid index
                        logger.debug("Deleting the invalid index {}".format(obj['name']))
                        cursor.execute("DROP INDEX {t};".format(t=obj['name']))
                        logger.debug("Renaming old index ({old}) back to original name ({t})".format(old=old_index_name, t=obj['name']))
                        cursor.execute("ALTER INDEX {old} RENAME TO {t};".format(t=obj['name'], old=old_index_name))

                        # Break out, we can't do anymore
                        break

                # Analyze the new index.
                cursor.execute("ANALYSE {t};".format(t=obj['name']))

                if obj['primary']:
                    if not always_drop_first:
                        cursor.execute("ALTER TABLE {table} DROP CONSTRAINT {t}_old;".format(t=obj['name'], table=obj['table']))

                    cursor.execute("ALTER TABLE {table} ADD CONSTRAINT {t} PRIMARY KEY USING INDEX {t};".format(t=obj['name'], table=obj['table']))

                if not always_drop_first:
                    logger.debug("Dropped index {old}".format(old=old_index_name))
                    cursor.execute("DROP INDEX {old};".format(old=old_index_name))

                newsize = index_size(cursor, obj['name'])
                savings = oldsize - newsize
                total_savings += savings
                logger.info("Saved {} {:.0%} - Total savings so far: {}".format(format_size(savings), savings/oldsize, format_size(total_savings)))


    if args.dry_run:
        logger.info("Finish. Ran in dry-run so no space saved")
    else:
        logger.info("Finish. Saved {} in total".format(format_size(total_savings)))

    if conn:
        conn.close()


if __name__ == '__main__':
    main()
