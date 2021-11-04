# Wikidata types for all entities, with corrections

## Prerequisites (check once per machine)

1. Download this repository, for example, with `git clone
   https://github.com/ad-freiburg/wiki_entity_linker`, then `cd
   wiki_entity_linker/wikidata-types` and make sure that the subdirectory
   `index` is world-writable (`chmod 777 index`).

2. Check if you have the rights to use `docker` on your machine. If not, use
   `wharfer` instead in the next step and also change the value of `DOCKER_CMD`
   in the Makefile to `wharfer`.

3. You need a docker image `qlever.master` of the current QLever code. If there
   is no such image on your machine, `git clone --recursive
   https://github.com/ad-freiburg/qlever && cd qlever` and build the image with
   `docker build -t qlever.master .`. If you don't have `docker` rights, you can
   use `wharfer` instead.

4. You need a running QLever instance for Wikidata under the URL specified by
   the variable `API_WIKIDATA` in the `Makefile` (by default, this is set to
   https://qlever.cs.uni-freiburg.de/api/wikidata).

5. You require about 25 GB of RAM and 100 GB of disk space. The six steps
   described in the next section take about one hour. Most of the time (about
   45 minutes) is used for Step 4 (building the index).

## Build a QLever instance and query it for the desired result

This directory contains a `Makefile`, with which the following sequence of steps
can be executed with `make all` or even shorter with just `make`. When you do
that, at the beginning, the name of the Makefile target for each step is shown
together with a short explanation. You can use these targets to execute one or
more steps individually, for example `make start wait gettypes`.

1. Download the predicates wdt:P31, wdt:P279, and @en@rdfs:label from a Qlever
   Wikidata instance (Makefile variable `API_WIKIDATA`)
2. Apply the corrections from file `corrections.txt` and produce a single TTL
   file `wikidata-types.ttl`
3. Build a QLever index from `wikidata-types.ttl`
4. Start a QLever instance based on that index
5. Wait for the backend to be ready
6. Issue query for all Wikidata entities and all their types from a given
   whitelist of types as listed in `types.txt`; the result for that query is
   written to a file `entity-types.ttl` (Makefile variable `ENTITY_TYPES_FILE`).
