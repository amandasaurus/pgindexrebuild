# pgindexrebuild

Reindexes a table and solves table bloat by creating a new index with the same
layout from scratch and then removing the old one. All indexes are created
CONCURRENTLY to minimize disruption to the database. This tool is designed to
be usable on production system.

It rebuilds smaller indexes first, so that the amount of available space will
increase by the time it gets to the larger indexes. Otherwise there might not
be enough disk space available to recreate the larger indexes.

This tool can take a long time to run.

# Installation

    pip install .

# Usage

    pgindexrebuild -d $DATABASE -U $USERNAME
