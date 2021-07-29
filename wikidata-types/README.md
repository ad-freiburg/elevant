# Wikidata types for all entities, with corrections

## Prerequisites

1. A running Qlever instance for Wikidata under the URL specified by the
   variable `API_WIKIDATA` in the `Makefile` (by default, this is set to
   https://qlever.cs.uni-freiburg.de/api/wikidata).

2. A docker image `qlever.master` of the current QLever code. If there is no
   such image on your machine, `git clone https://github.com/ad-freiburg/qlever
   && cd qlever` and build the image with `docker build -t qlever.master .`.

2. You require about 25 GB of RAM and 100 GB of disk space.

## Build a QLever instance and query it

This directory contains a `Makefile` with the following functionality (which can
be invoked via simple Makefile targets, see below).

1. Download the predicates wdt:P31, wdt:P279, and @en@rdfs:label from a Qlever
   Wikidata instance (Makefile variable `API_WIKIDATA`)
2. Apply the corrections from file `corrections.txt` and produce a single TTL
   file `wikidata-types.ttl`
3. Build a QLever index from `wikidata-types.ttl`
4. Start a QLever instance based on that index

5. Issue query to that instance for all Wikidata entities and all their types
   from a given whiteliste of types as listed in `types.txt`; the result for
   that query is written to a file `entity-types.ttl`

Steps 1 - 4 can be executed with `make qlever-instance`. These steps take about
one hour, most of it used for Step 3.

For Step 5, wait until the QLever instance is ready (check with `make log`, this
shows the tail of the log, you can exit with Ctrl+C). Then do `make entity-types`.
This step takes about 5 minutes.