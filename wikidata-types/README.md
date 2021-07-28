# Wikidata types for all entities, with corrections

This directory a `Makefile` with the following functionality:

1. Download the predicates wdt:P31, wdt:P279, and @en@rdfs:label from a Qlever
   Wikidata instance (Makefile variable `API_WIKIDATA`)
2. Apply the corrections from file `corrections.txt` and produce a single TTL
   file `wikidata-types.ttl`
3. Build a QLever index from `wikidata-types.ttl`
4. Start a QLever instance based on that index
5. Issue query to that instance for all Wikidata entities and all their types
   from a given whiteliste of types as listed in `types.txt`; the result for
   that query is written to a file `entity-types.ttl`

As preparation, clone the repository https://github.com/ad-freiburg/qlever-proxy
in directory `/local/data/qlever/qlever-indices/qlever-proxy`. On many of our
machines, that directory already exists. If you choose a different directory,
change the "include" in the first line of the `Makefile` accordingly.

Steps 1 - 4 can be executed with `make all`.

For Step 5, wait until the QLever instance is ready (check with `make log`, this
shows the tail of the log, you can exit with Ctrl+C). Then do `make entity-types`.
