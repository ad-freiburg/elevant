SHELL = /bin/bash
DOCKER_CMD = docker

.PHONY: index

DB = wikidata-types
API_WIKIDATA_TYPES = http://localhost:$(PORT)
DOCKER_IMAGE = qlever.master
DOCKER_CONTAINER = qlever.$(DB)
MEMORY_FOR_QUERIES = 20
CACHE_MAX_SIZE_GB = 10
CACHE_MAX_SIZE_GB_SINGLE_ENTRY = 5
CACHE_MAX_NUM_ENTRIES = 100
PORT = 7016

API_WIKIDATA = https://qlever.cs.uni-freiburg.de/api/wikidata
CORRECTIONS_FILE = corrections.txt  
TYPES_FILE = types.txt
ENTITY_TYPES_FILE = entity-types.ttl
PREDICATES = wdt:P279 wdt:P31 @en@rdfs:label

BATCH_SIZE = 10000000
MAX_RESULT_SIZE = $(shell echo "200 * $(BATCH_SIZE)" | bc)
TYPES_WHITELIST = $(shell cat types.txt | sed 's/\s*\#.*$$//g')

# Do it all in one target (see text in echo commands).
#
# NOTE: Since this is the first target, just typing  make  is sufficient.
all:
	@echo
	@echo "The following steps will be taken (Makefile target in square brackets):"
	@echo
	@echo "[getdata]  Get each of $(PREDICATES) from $(API_WIKIDATA)"
	@echo "[ttl]      Apply corrections (ADD and REMOVE) from $(CORRECTIONS_FILE)"
	@echo "[index]    Build index from resulting file $(DB).ttl"
	@echo "[start]    Start backend for that index on port $(PORT)"
	@echo "[wait]     Wait for the backend to be up"
	@echo "[gettypes] Launch the entity-types query, write result to $(ENTITY_TYPES_FILE)"
	@echo
	@SECONDS=0; \
	  $(MAKE) -s getdata ttl index start wait gettypes; \
	  echo; echo "Total time needed: $$(($$SECONDS / 60)) min"
	@echo

config:
	@for VAR in API_WIKIDATA API_WIKIDATA_TYPES \
	  MEMORY_FOR_QUERIES CACHE_MAX_SIZE_GB \
	  CACHE_MAX_SIZE_GB_SINGLE_ENTRY CACHE_MAX_NUM_ENTRIES \
	  ;do printf "%-30s = %s\n" "$$VAR" "$${!VAR}"; done
	@echo
	@for VAR in BATCH_SIZE MAX_RESULT_SIZE \
	  ;do printf "%-30s = %'15d\n" "$$VAR" "$${!VAR}"; done

# Target for the first four steps.
qlever-instance:
	$(MAKE) -s getdata ttl index start

index:
	time ( $(DOCKER_CMD) run -it --rm -v $(shell pwd):/pwd --entrypoint bash --name qlever.$(DB)-index $(DOCKER_IMAGE) -c "IndexBuilderMain -f /pwd/$(DB).ttl -i /pwd/index/$(DB) -s /pwd/qlever.settings.json"; rm -f $(DB)*tmp* )

start:
	echo "Starting QLever backend (and removing previous container if there is one)"
	-$(DOCKER_CMD) rm -f qlever.$(DB)
	$(DOCKER_CMD) run -d --restart=unless-stopped -v $(shell pwd)/index:/index -p $(PORT):7001 -e INDEX_PREFIX=$(DB) -e MEMORY_FOR_QUERIES=$(MEMORY_FOR_QUERIES) -e CACHE_MAX_SIZE_GB=${CACHE_MAX_SIZE_GB} -e CACHE_MAX_SIZE_GB_SINGLE_ENTRY=${CACHE_MAX_SIZE_GB_SINGLE_ENTRY} -e CACHE_MAX_NUM_ENTRIES=${CACHE_MAX_NUM_ENTRIES} --name $(DOCKER_CONTAINER) $(DOCKER_IMAGE)

stop:
	$(DOCKER_CMD) stop qlever.$(DB)

log:
	$(DOCKER_CMD) logs -f qlever.$(DB)

# Wait until QLever backend connects to query.
wait:
	@printf "Waiting for QLever backend "; \
	  while [ $$(curl --silent $(API_WIKIDATA_TYPES) > /dev/null; echo $$?) != 0 ]; \
	    do printf "."; sleep 10; done; echo

# Build TTL with $(PREFIXES) from TTL files obtained via getdata: target.
ttl:
	echo "$$PREFIXES" | sed 's/^PREFIX\s\+\(.*\)/@prefix \1 ./' > $(DB).ttl
	cat $(CORRECTIONS_FILE) | sed -n 's/\s\+#.*//; s/^ADD\s\+\(.*\)/\1 ./p' > add-triples.ttl
	cat $(CORRECTIONS_FILE) | sed -n 's/\s\+#.*//; s/^REMOVE\s\+\(.*\)/\1 ./p' > remove-triples.ttl
	cat add-triples.ttl >> $(DB).ttl
	for PREDICATE in $(PREDICATES); do \
	  grep -v -f remove-triples.ttl $$PREDICATE.ttl >> $(DB).ttl; done
	wc -l $(DB).ttl | numfmt --grouping

# Get data for $(PREDICATES) via $(API_WIKIDATA) and write to ttl files.
getdata:
	for PREDICATE in $(PREDICATES); do \
	  $(MAKE) -sB API=$$API_WIKIDATA PREDICATE=$$PREDICATE QUERY_VARIABLE=PREDICATE_QUERY OUTFILE=$$PREDICATE.ttl query.batched; done

# Get result for $(QUERY) in batches of size $(BATCH_SIZE), using query: target
query.batched:
	$(info $(API))
	$(info $(PREFIXES))
	$(info $($(QUERY_VARIABLE)))
	@true > $(OUTFILE)
	@RESULT_SIZE=`$(MAKE) -s QUERY="$(shell echo ${$(QUERY_VARIABLE)})" count`; \
	for OFFSET in `seq 0 $$BATCH_SIZE $$RESULT_SIZE`; do \
	  echo "LIMIT $$BATCH_SIZE OFFSET $$OFFSET"; \
	  $(MAKE) -s QUERY="$(shell echo ${$(QUERY_VARIABLE)}) LIMIT $$BATCH_SIZE OFFSET $$OFFSET" query; \
	done

# Get results for $(QUERY), convert to ttl (without prefixes), and append to $(OUTFILE)
query:
	curl -Gs $(API) \
	    --data-urlencode "query=$$PREFIXES $(QUERY)" \
	    --data-urlencode "action=tsv_export" \
	    | sed 's/http:\/\/www.wikidata.org\///g;' \
	    | sed 's/entity\//wd:/g; s/prop\/direct\//wdt:/g;' \
	    | sed 's/http:\/\/www\.w3\.org\/2000\/01\/rdf-schema#/rdfs:/; s/@en@//; s/"@en/"/' \
	    | sed 's/[<>]//g' \
	    | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t\\"/\t"/; s/\t/ /g; s/\\"$$/"/; s/$$/ ./' \
	    >> $(OUTFILE)

# Get result size for $(QUERY), without downloading anything of the result yet
count:
	curl -Gs $(API) \
	    --data-urlencode "query=$$PREFIXES $(QUERY) LIMIT 0" \
	    --data-urlencode "send=0" \
	    | grep resultsize | head -1 | sed 's/[^0-9]//g'

clearcache:
	curl -Gs $(API_WIKIDATA_TYPES) --data-urlencode "cmd=clearcachecomplete" > /dev/null


# Get the types for all entities as TTL
gettypes:
	$(MAKE) -s API=$$API_WIKIDATA_TYPES QUERY_VARIABLE=ENTITY_TYPES_QUERY OUTFILE=$(ENTITY_TYPES_FILE) query.batched
	wc -l $@.ttl | numfmt --grouping



define PREFIXES
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
endef

define PREDICATE_QUERY
SELECT ?s ?p ?o WHERE { VALUES ?p { $(PREDICATE) } ?s ?p ?o }
endef

define ENTITY_TYPES_QUERY
SELECT DISTINCT ?item ?type WHERE { {
    VALUES ?type { $(TYPES_WHITELIST) }
    ?item wdt:P31 ?type
  } UNION {
    VALUES ?type { $(TYPES_WHITELIST) }
    ?item wdt:P31 ?m . ?m wdt:P279+ ?type
} }
endef

define ENTITY_NAME_AND_ALIAS_PATTERN
?qleverui_entity rdfs:label . BIND(?qleverui_entity AS ?alias)
endef

define ENTITY_SCORE_PATTERN
{ SELECT ?qleverui_entity (COUNT(?qleverui_tmp) AS ?count) WHERE { ?qleverui_entity wdt:P31 ?qleverui_tmp } GROUP BY ?qleverui_entity }
endef

export
