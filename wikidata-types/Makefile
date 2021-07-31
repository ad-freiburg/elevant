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
DATA_QUERY_NAMES = P279 P31
# DATA_QUERY_NAMES = P279 P31 LABEL SITELINKS

BATCH_SIZE = 10000000
MAX_RESULT_SIZE = $(shell echo "200 * $(BATCH_SIZE)" | bc)
TYPES_WHITELIST = $(shell cat types.txt | sed 's/\s*\#.*$$//g')
SED_PREFIX_SUBSTITUTIONS = $(shell echo "$(PREFIXES)" | sed 's|\([.]\)|\\\1|g; s/PREFIX \+\([^ ]\+\) \+<\([^ ]\+\)>/s|<\2|\1|g; /g;')


# Do it all in one target (see text in echo commands).
#
# NOTE: Since this is the first target, just typing  make  is sufficient.
all:
	@echo
	@echo "The following steps will be taken (Makefile target in square brackets):"
	@echo
	@echo "[getdata]  Get results for $(DATA_QUERY_NAMES) from $(API_WIKIDATA)"
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
	@echo
	@echo "[index] Build QLever index from $(DB).ttl"
	@echo
	time ( $(DOCKER_CMD) run -it --rm -v $(shell pwd):/pwd --entrypoint bash --name qlever.$(DB)-index $(DOCKER_IMAGE) -c "IndexBuilderMain -f /pwd/$(DB).ttl -i /pwd/index/$(DB) -s /pwd/qlever.settings.json"; rm -f $(DB)*tmp* )
	@echo

start:
	@echo
	@echo "[start] Starting QLever backend (and removing previous container if there is one)"
	@echo
	-$(DOCKER_CMD) rm -f qlever.$(DB)
	$(DOCKER_CMD) run -d --restart=unless-stopped -v $(shell pwd)/index:/index -p $(PORT):7001 -e INDEX_PREFIX=$(DB) -e MEMORY_FOR_QUERIES=$(MEMORY_FOR_QUERIES) -e CACHE_MAX_SIZE_GB=${CACHE_MAX_SIZE_GB} -e CACHE_MAX_SIZE_GB_SINGLE_ENTRY=${CACHE_MAX_SIZE_GB_SINGLE_ENTRY} -e CACHE_MAX_NUM_ENTRIES=${CACHE_MAX_NUM_ENTRIES} --name $(DOCKER_CONTAINER) $(DOCKER_IMAGE)
	@echo

stop:
	$(DOCKER_CMD) stop qlever.$(DB)

log:
	$(DOCKER_CMD) logs -f qlever.$(DB)


# Wait until QLever backend connects to query.
wait:
	@echo
	@echo "[wait] Waiting for QLever backend (one dot = 10 seconds)"
	@echo
	@while [ $$(curl --silent $(API_WIKIDATA_TYPES) > /dev/null; echo $$?) != 0 ]; \
	  do printf "."; sleep 10; done; echo
	@echo

# Build TTL with $(PREFIXES) from TTL files obtained via getdata: target.
ttl:
	@echo
	@echo "[ttl] Build $(DB).ttl from results for $(DATA_QUERY_NAMES)"
	@echo
	echo "$${PREFIXES}" | sed 's/^PREFIX\s\+\(.*\)/@prefix \1 ./' > $(DB).ttl
	cat $(CORRECTIONS_FILE) | sed -n 's/\s\+#.*//; s/^ADD\s\+\(.*\)/\1 ./p' > add-triples.ttl
	cat $(CORRECTIONS_FILE) | sed -n 's/\s\+#.*//; s/^REMOVE\s\+\(.*\)/\1 ./p' > remove-triples.ttl
	cat add-triples.ttl >> $(DB).ttl
	for QUERY_NAME in $(DATA_QUERY_NAMES); do \
	  grep -v -f remove-triples.ttl $${QUERY_NAME}.ttl >> $(DB).ttl; done
	wc -l $(DB).ttl | numfmt --grouping
	@echo "First and last five lines of $(DB).ttl are:"
	@head -5 $(DB).ttl && tail -5 $(DB).ttl
	@echo

# Get data for queries from $(DATA_QUERY_VARABLES) via $(API_WIKIDATA) and write to ttl files.
getdata:
	@echo
	@echo "[getdata] Get data for given queries in batches"
	@echo
	@echo "DATA_QUERY_NAMES = $(DATA_QUERY_NAMES)"
	for QUERY_NAME in $(DATA_QUERY_NAMES); do echo; \
	  $(MAKE) -sB API=$$API_WIKIDATA QUERY_VARIABLE=$${QUERY_NAME}_QUERY OUTFILE=$${QUERY_NAME}.ttl query.batched; done
	@echo

# Get result for $(QUERY) in batches of size $(BATCH_SIZE), using query: target
query.batched:
	echo "API = $(API)"
	$(info $(PREFIXES))
	$(info $($(QUERY_VARIABLE)))
	@true > $(OUTFILE)
	@RESULT_SIZE=$$($(MAKE) -s QUERY="$(shell echo ${$(QUERY_VARIABLE)})" count); \
	echo "Result size = $$(echo $$RESULT_SIZE | numfmt --grouping)"; \
	for OFFSET in `seq 0 $$BATCH_SIZE $$RESULT_SIZE`; do \
	  echo "LIMIT $$BATCH_SIZE OFFSET $$OFFSET"; \
	  $(MAKE) -s QUERY="$(shell echo ${$(QUERY_VARIABLE)}) LIMIT $$BATCH_SIZE OFFSET $$OFFSET" query; \
	done
	@echo "First line and last line of $(OUTFILE) are:"
	@head -1 $(OUTFILE) && tail -1 $(OUTFILE)

# Get results for $(QUERY), convert to ttl (without prefixes), and append to $(OUTFILE)
#
# NOTE: Here is a short description of what each of the five sed lines does.
# Test with  make DATA_QUERY_NAMES=TEST getdata && head TEST.ttl
#
# 1. Add TAB and . at the end and TAB before ^^ and @
# 2. Remove language prefixes (@en@) ... see comment below
# 3. Replace prefixes from $(PREFIXES) by their short name (it's magic)
# 4. Escape \ everywhere (only occurs within literas) and " inside of literals
# 5. Remove > before TAB, remove TAB before ^ and @, replace TABs by spaces
#
# Currently not removing types (^^<...>) and language tags (@en) after literals,
# here are the required sed substitutions: s/\^\^<.*>\t/\t/; s/"@[a-z]\+/"/g
query:
	@curl -Gs $(API) \
	    --data-urlencode "query=$$PREFIXES $(QUERY)" \
	    --data-urlencode "action=tsv_export" \
	    | sed 's/$$/\t./; s/\^\^<\([^>]\+\)>\t/\t^^<\1>\t/g; s/"\(@[a-z]\+\)\t/"\t\1\t/g' \
	    | sed 's/\t@[a-z]\+@/\t/g' \
	    | sed '$(SED_PREFIX_SUBSTITUTIONS)' \
	    | sed 's/\\/\\\\/g; s/\t"/\t\x01/g; s/"\t/\x01\t/g; s/"/\\"/g; s/\x01/"/g' \
	    | sed 's/>\t/\t/g; s/\t\([\^@]\)/\1/g; s/\t/ /g' \
	    >> $(OUTFILE)

# Get result size for $(QUERY), without downloading anything of the result yet
count:
	curl -Gs $(API) \
	    --data-urlencode "query=$$PREFIXES $(QUERY) LIMIT 0" \
	    --data-urlencode "send=0" \
	    | grep resultsize | head -1 | sed 's/[^0-9]//g'

clearcache:
	curl -Gs $(API_WIKIDATA_TYPES) --data-urlencode "cmd=clearcachecomplete" > /dev/null

warmup:
	# docker exec -it qlever-ui bash -c "python manage.py warmup $(DB)"
	curl -Gs $(API_WIKIDATA_TYPES) --data-urlencode "query=$$PREFIXES $(WARMUP_QUERY_1) LIMIT 0" --data-urlencode "pinresult=true" > /dev/null
	curl -Gs $(API_WIKIDATA_TYPES) --data-urlencode "query=$$PREFIXES $(WARMUP_QUERY_2) LIMIT 0" --data-urlencode "pinresult=true" > /dev/null
	curl -Gs $(API_WIKIDATA_TYPES) --data-urlencode "query=$$PREFIXES $(WARMUP_QUERY_3) LIMIT 0" --data-urlencode "pinresult=true" > /dev/null
	


# Get the types for all entities as TTL
gettypes:
	@echo
	@echo "[gettypes] Get entity types via batched query to $(API_WIKIDATA_TYPES)"
	@echo
	$(MAKE) -s API=$$API_WIKIDATA_TYPES QUERY_VARIABLE=ENTITY_TYPES_QUERY OUTFILE=$(ENTITY_TYPES_FILE) query.batched
	@wc -l $(ENTITY_TYPES_FILE) | numfmt --grouping
	@echo "First and last line of $(ENTITY_TYPES_FILE) are:"
	@head -1 $(ENTITY_TYPES_FILE) && tail -1 $(ENTITY_TYPES_FILE)
	@echo


define PREFIXES
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
endef

define P31_QUERY
SELECT ?s ?p ?o WHERE { VALUES ?p { wdt:P31 } ?s ?p ?o }
endef

define P279_QUERY
SELECT ?s ?p ?o WHERE { VALUES ?p { wdt:P279 } ?s ?p ?o }
endef

define LABEL_QUERY
SELECT ?s ?p ?o WHERE { VALUES ?p { @en@rdfs:label } ?s ?p ?o }
endef

define SITELINKS_QUERY
SELECT ?s ?p ?o WHERE { VALUES ?p { wikibase:sitelinks } ?m schema:about ?s . ?m ?p ?o }
endef

define TEST_QUERY
SELECT ?s ?p ?o ?l WHERE { VALUES ?p { wdt:P1082 } ?s ?p ?o . ?s @en@rdfs:label ?l }
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

define WARMUP_QUERY_1
SELECT ?s ?p ?o WHERE { { VALUES ?p { wdt:P31 } ?s ?p ?o } UNION { VALUES ?p { wdt:P279 } ?s ?p ?o } } ORDER BY ASC(?s)
endef

define WARMUP_QUERY_2
SELECT ?s ?o WHERE { ?s rdfs:label ?o }
endef

define WARMUP_QUERY_3
SELECT ?s ?o WHERE { ?s wdt:P279+ ?o } ORDER BY ASC(?s)
endef

define ENTITY_NAME_AND_ALIAS_PATTERN
?qleverui_entity rdfs:label . BIND(?qleverui_entity AS ?alias)
endef

define ENTITY_SCORE_PATTERN
{ SELECT ?qleverui_entity (COUNT(?qleverui_tmp) AS ?count) WHERE { ?qleverui_entity wdt:P31 ?qleverui_tmp } GROUP BY ?qleverui_entity }
endef

export
