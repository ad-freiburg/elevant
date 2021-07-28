include /local/data/qlever/qlever-proxy/ac-queries.Makefile

.PHONY: index

DB = wikidata-types
API = https://qlever.cs.uni-freiburg.de/api/wikidata-types
DOCKER_IMAGE = qlever.master
MEMORY_FOR_QUERIES = 30
CACHE_MAX_SIZE_GB = 10
CACHE_MAX_SIZE_GB_SINGLE_ENTRY = 5
CACHE_MAX_NUM_ENTRIES = 100
PORT = 7016

API_WIKIDATA = https://qlever.cs.uni-freiburg.de/api/wikidata
CORRECTIONS_FILE = corrections.txt  
TYPES_WHITELIST = $(shell cat types.txt | sed 's/\s*\#.*$$//g')
PREDICATES = wdt:P279 wdt:P31 @en@rdfs:label
# PREDICATES = wdt:P279
BATCH_SIZE = 5000000
MAX_RESULT_SIZE = $(shell echo "200 * $(BATCH_SIZE)" | bc)


config:
	@for VAR in API_WIKIDATA \
	  ;do printf "%-30s = %s\n" "$$VAR" "$${!VAR}"; done
	@for VAR in BATCH_SIZE MAX_RESULT_SIZE \
	  ;do printf "%-30s = %'15d\n" "$$VAR" "$${!VAR}"; done

qlever-instance:
	@echo "The following steps will be taken:"
	@echo
	@echo "1. Get each of $(PREDICATES) from $(API_WIKIDATA)"
	@echo "2. Apply corrections (ADD and REMOVE) from $(CORRECTIONS_FILE)"
	@echo "3. Build index from resulting file $(DB).ttl"
	@echo "4. Start backend for that index on port $(PORT)"
	@echo
	$(MAKE) -s getdata # STEP 1
	@echo
	$(MAKE) -s ttl     # STEP 2
	@echo
	$(MAKE) -s index   # STEP 3
	@echo
	$(MAKE) -s start   # STEP 4

index:
	time ( docker run -it --rm -v $(shell pwd):/pwd --entrypoint bash --name qlever.$(DB)-index $(DOCKER_IMAGE) -c "IndexBuilderMain -f /pwd/$(DB).ttl -i /pwd/index/$(DB) -s /pwd/qlever.settings.json"; rm -f $(DB)*tmp* )


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
	  $(MAKE) -sB PREDICATE=$$PREDICATE QUERY_VARIABLE=PREDICATE_QUERY OUTFILE=$$PREDICATE.ttl query.batched; done

# Get result for $(QUERY) in batches of size $(BATCH_SIZE), using query: target
query.batched:
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
	curl -Gs $(API_WIKIDATA) \
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
	curl -Gs $(API_WIKIDATA) \
	    --data-urlencode "query=$$PREFIXES $(QUERY) LIMIT 0" \
	    --data-urlencode "send=0" \
	    | head -10 | grep resultsize | sed 's/[^0-9]//g'

# Get the types for all entities as TTL
entity-types:
	  $(MAKE) -s QUERY_VARIABLE=ENTITY_TYPES_QUERY OUTFILE=entity-types.ttl query.batched



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
