# pgindexrebuild

[![PyPI](https://img.shields.io/pypi/v/pgindexrebuild.svg?maxAge=2592000)]()
[![PyPI](https://img.shields.io/pypi/l/pgindexrebuild.svg?maxAge=2592000)]()

Reindexes an index and solves index bloat by creating anew a new index with the
same definition and only afterwards removing the old one. All indexes are
created CONCURRENTLY to minimize disruption to the database.

This tool is designed to be usable on a production system. At all times there
is an index there for your queries to use, and indexes are created CONCURRENTLY
so writes can process normally.

It rebuilds smaller indexes first, which reduces the risk of larger indexes
being unable to run due to lack of disk space.

This tool can take a long time to run.

## Installation

    pip install .

## Usage

    pgindexrebuild -d $DATABASE -U $USERNAME

See `pgindexrebuild --help` for the full listing of options. Use `--dry-run` to
not change anything, merely see what would be done.

## Copyright

Copyright 2016 Rory McCann <rory@technomancy.org> - Licenced under the GNU GPL v3 or later

## See also

 * [pgtoolkit](https://github.com/grayhemp/pgtoolkit) which does something
   similar for table bloat, and can also run on a production database
