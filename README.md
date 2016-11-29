# pgindexrebuild - Production friendly PostgreSQL Index debloater!

[![PyPI](https://img.shields.io/pypi/v/pgindexrebuild.svg?maxAge=2592000)]()
[![PyPI](https://img.shields.io/pypi/l/pgindexrebuild.svg?maxAge=2592000)]()

Reindexes an index and solves index bloat by creating anew a new index with the
same definition and only afterwards removing the old one. All indexes are
created CONCURRENTLY to minimize disruption to the database. The (old bloated)
index can still be used for queries. The table can be read from and written to.

This tool is designed to be usable on a production system. At all times there
is an index there for your queries to use, and indexes are created CONCURRENTLY
so writes can process normally.

It rebuilds smaller indexes first, which reduces the risk of larger indexes
being unable to run due to lack of disk space.

This tool can take a long time to run. It was written for the PostgreSQL 9.x version.

## Installation

    pip install pgindexrebuild

### psycopg2

You need [`psycopg2`](http://initd.org/psycopg/) installed. Pip will try to
install it with the above command. On Debian/Ubuntu you can `apt-get install
python-psycopg2` and you don't need to installed the required
`postgresql-server-dev-X.Y` and compiler packages.

## Usage

    pgindexrebuild -d $DATABASE [-U $USERNAME]

See `pgindexrebuild --help` for the full listing of options. Use `--dry-run` to
not change anything, merely see what would be done.

### Conditional reindexing

The `--min-bloat` controls what indexes to reindex. `--min-bloat 1G` will only
reindex indexes which have at least 1GB of bloat.

### Locking

Use `--lock-file /path/to/some/file` to use [python's build in file
locking](https://docs.python.org/2/library/fcntl.html) to prevent more than one
instance of this programme running at once.

### Logging

By default it logs to standard out, and syslog. Use `--no-log-stdout` /
`--no-log-syslog` to disable that.

### When you have no space to reindex

If your disk is full, you will not have the space to create the new index. Use
the `always-drop-first`, and it will drop the old (bloated) index first, and
then create the new index. There will be no index during the index creation, so
**this option will degrade your database performance**, use it only if you
don't have the disk available to do a normal index rebuild.

### Invalid Indexes

When an index is created with `CONCURRENTLY` and something goes wrong, the
index will be "invalid" and cannot be used. This new (useless) index will still
use up disk space. After creating an index, this programme will check if the
new index is valid, and if not, it will remove the invalid index and try to
recreate it again. It will try up to 10 times before giving up, when it when
then leave behind the bloated, but working, index.

It's possible that there might be a bug in this programme and it will
incorrectly think the new invalid index is OK, and remove the working, bloated
index. This has happened to the developer a few times.

If you pass the `--repair-invalid` argument, then it will also rebuild
(concurrently) any invalid indexes it finds in your database. This option can
be used as a way to repair any problems that this programme might have caused
in a previous run.

By default it will not rebuild any invalid indexes.

## Copyright

Copyright © 2016 Rory McCann <rory@technomancy.org> - Licenced under the GNU GPL v3 or later

### Hacking / Contributing

Contributions are always welcome.

## See also

 * [pgtoolkit](https://github.com/grayhemp/pgtoolkit) which does something
   similar for table bloat, and can also run on a production database
