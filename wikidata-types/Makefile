SHELL = /bin/bash
DOCKER_CMD = docker

.PHONY: index

DB = wikidata-types
API_WIKIDATA_TYPES = http://localhost:$(PORT)
DOCKER_IMAGE = qlever.master
DOCKER_CONTAINER = qlever.$(DB)
MEMORY_FOR_QUERIES = 50GB
CACHE_MAX_SIZE_GB = 30GB
CACHE_MAX_SIZE_GB_SINGLE_ENTRY = 10GB
CACHE_MAX_NUM_ENTRIES = 100
PORT = 7016

API_WIKIDATA = https://qlever.cs.uni-freiburg.de/api/wikidata
CORRECTIONS_FILE = corrections.txt
TYPES_FILE = types.tsv
ENTITY_TYPES_FILE = entity-types.tsv
# DATA_QUERY_NAMES = P279 P31
DATA_QUERY_NAMES = P279 P31 LABEL SITELINKS

BATCH_SIZE = 10000000
MAX_RESULT_SIZE = $(shell echo "200 * $(BATCH_SIZE)" | bc)
TYPES_WHITELIST = $(shell cat $(TYPES_FILE) | sed -r 's/(Q[0-9]*)\s*.*/wd:\1/g')
SED_PREFIX_SUBSTITUTIONS = $(shell echo "$(PREFIXES)" | sed 's|\([.]\)|\\\1|g; s/PREFIX \+\([^ ]\+\) \+<\([^ ]\+\)>/s|<\2|\1|g; /g;')

# Variants of getting the contents of a variable with a multiline value (see the
# define ... endef at the end of this file for several variables with such
# values). Some of these DON'T work, see the explanations.
#
# 1.  $(info $(VARIABLE))		value with newlines
# 2.  $(subst $(NL), ,$(VARIABLE))      value with spaces instead of newlines
# 3.  echo $(VARIABLE)       		DOES NOT WORK
# 4.  echo "$(VARIABLE)"     		DOES NOT WORK
# 5.  echo $${VARIABLE}			like 4, with shell variable
# 6.  echo "$${VARIABLE}"		like 1, with shell variable
# 7.  echo "$${VARIABLE//$$'\n'/ }"	like 4, with shell variable
#
# Note that to be able to use $${VARIABLE}, there has to be a line with "export"
# (without the quotes) in the Makefile.
#
# @1: Print the value as is; can't use in command because of the newlines
# @2: The value with spaces instead of newlines; this assumes a definition of NL
# as a newline (define <two empty lines> endef, see below)
# @3: Error message because the newline is interpreted as the end of the command
# @4: Error message for the same reasons (the "..." does not change this)
# @5: Value with newlines replaced by spaces (echo just splits the value by
# whitespace and then outputs the fields separated by spaces)
# @6: Value with newlines intact
# @7: Same output as 4, but by explicitly replacing each newline with a space
# (note the // for replacing all occurrences and the $$ because $ has to be
# escaped in a Makefile)
#
# TODO: How to assign a value of a Makefile variable with newlines to another
# Makefile variable? The following does NOT work (because of the newline)
#
# QUERY = $(WARMUP_QUERY_1)


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
	  $(MAKE) -sB API=$$API_WIKIDATA QUERY_VARIABLE=$${QUERY_NAME}_QUERY OUTFILE=$${QUERY_NAME}.ttl query; done
	@echo

# Get results for $(QUERY), convert to ttl (without prefixes), and append to $(OUTFILE)
#
# NOTE: Here is a short description of what each of the five sed lines does.
# Test with  make DATA_QUERY_NAMES=TEST getdata && head TEST.ttl
#
# 0. Drop lines that start with ? (first line with column names)
# 1. Add TAB and . at the end and TAB before ^^ and @
# 2. Remove language prefixes (@en@) ... see comment below
# 3. Replace prefixes from $(PREFIXES) by their short name (it's magic)
# 4. Escape \ everywhere (only occurs within literas) and " inside of literals
# 5. Remove > before TAB, remove TAB before ^ and @, replace TABs by spaces
#
# Currently not removing types (^^<...>) and language tags (@en) after literals,
# here are the required sed substitutions: s/\^\^<.*>\t/\t/; s/"@[a-z]\+/"/g
query:
	@echo "API = ${API}"
	@echo "OUTFILE = ${OUTFILE}"
	@echo $$PREFIXES
	@echo $${${QUERY_VARIABLE}}
	@curl -Gs $(API) \
	    --data-urlencode "query=$$PREFIXES $${${QUERY_VARIABLE}}" \
	    --data-urlencode "action=tsv_export" \
	    | sed -r '/^[?]/d' \
	    | sed 's/$$/\t./; s/\^\^<\([^>]\+\)>\t/\t^^<\1>\t/g; s/"\(@[a-z]\+\)\t/"\t\1\t/g' \
	    | sed 's/\t@[a-z]\+@/\t/g' \
	    | sed '$(SED_PREFIX_SUBSTITUTIONS)' \
	    | sed 's/\\/\\\\/g; s/\t"/\t\x01/g; s/"\t/\x01\t/g; s/"/\\"/g; s/\x01/"/g' \
	    | sed 's/>\t/\t/g; s/\t\([\^@]\)/\1/g; s/\t/ /g' \
	    > ${OUTFILE}
	@echo "First line and last line of ${OUTFILE} are:"
	@head -1 ${OUTFILE} && tail -1 ${OUTFILE}
	@echo

# Get result size for $(QUERY), without downloading anything of the result yet
count:
	curl -Gs $(API) \
	    --data-urlencode "query=$$PREFIXES $(QUERY) LIMIT 0" \
	    --data-urlencode "send=0" \
	    | grep resultsize | head -1 | sed 's/[^0-9]//g'

clearcache:
	curl -Gs $(API_WIKIDATA_TYPES) --data-urlencode "cmd=clearcachecomplete" > /dev/null

# NOTE: Explanation of the $${!WARMUP_QUERY_VARIABLE//$$'\n'/ }
#
# 1. In bash, ${!X} says to consider the value of X as a variable name and take
# its value; for example, WARMUP_QUERY_VARIABLE could be WARMUP_QUERY_1, and
# its value is a SPARQL query.
# 2. The // part replaces *each* newlines (with a single / it would be only the
# first newline) by a space; note that $'\n' is the standard bash way to get a
# newline character
# 3. The $$ instead of $ are needed because $ has a special meaning in a
# Makefile and needs to be escaped.
warmup:
	@echo
	@echo -e "\033[1mAC warmup queries\033[0m"
	@docker exec -it qlever-ui bash -c "python manage.py warmup $(DB) pin"
	@echo
	@echo -e "\033[1mCustom warumup queries\033[0m"
	@echo
	@for I in $(shell seq 1 100); do \
	  QUERY_VARIABLE=WARMUP_QUERY_$$I; \
	  QUERY=$${!QUERY_VARIABLE//$$'\n'/ }; \
	  if [ ! -z "$$QUERY" ]; then \
	    echo "$$QUERY"; \
	    $(MAKE) -s QUERY="$$QUERY" warmup.single-query; \
	    printf "\033[34mResult size = %s\033[0m\n" \
	      $$($(MAKE) -s API=$(API_WIKIDATA_TYPES) QUERY="$$QUERY" count | numfmt --grouping); \
	    echo; fi; done

warmup.single-query:
	curl -Gs $(API_WIKIDATA_TYPES) \
	  --data-urlencode "query=$$PREFIXES $$QUERY LIMIT 0" \
	  --data-urlencode "pinresult=true"\
	  > /dev/null

	
# Alternative way to get the value of a variable referenced by variable with
# spaces instead of newlines.
#
# echo "$(shell echo "${$(WARMUP_QUERY_VARIABLE)}")"
#
# 1. The inner "..." are needed because $($(WARMUP_QUERY_VARIABLE)) can contain
# symbols like ( or ) which are interpreted by the shell
# 2. With just the "$($(WARMUP_QUERY_VARIABLE))", if there is a newline in the
# query, this fails because there cannot be a newline within a "...". With the
# $(shell echo ...) newlines are converted to spaces (TODO: explain why).
# 3. The outer spaces are needed for the same reason as explained in 1: to avoid
# interpretation of symbols like ( or )


# Get the types for all entities as TTL
gettypes:
	@echo
	@echo "[gettypes] Get entity types via query to $(API_WIKIDATA_TYPES)"
	@echo
	$(MAKE) -s API=$$API_WIKIDATA_TYPES QUERY_VARIABLE=ENTITY_TYPES_QUERY OUTFILE=$(ENTITY_TYPES_FILE) query
	@sed -i '/wd:[^Q]/d' $(ENTITY_TYPES_FILE)
	@sed -i -r 's|wd:([^ ]*) wd:([^ ]*) .|\1	\2|' $(ENTITY_TYPES_FILE)
	@wc -l $(ENTITY_TYPES_FILE) | numfmt --grouping
	@echo "First and last line of $(ENTITY_TYPES_FILE) are:"
	@head -1 $(ENTITY_TYPES_FILE) && tail -1 $(ENTITY_TYPES_FILE)
	@echo



define NL


endef

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
SELECT ?s ?p ?o WHERE
{ { VALUES ?p { wdt:P31 } ?s ?p ?o } UNION { VALUES ?p { wdt:P279 } ?s ?p ?o } }
ORDER BY ASC(?s)
endef

define WARMUP_QUERY_2
SELECT ?s ?o WHERE { ?s rdfs:label ?o } ORDER BY ?s
endef

define WARMUP_QUERY_3
SELECT ?s ?o WHERE { ?s rdfs:label ?o } ORDER BY ?o
endef

define WARMUP_QUERY_4
SELECT ?s ?o WHERE { ?s wikibase:sitelinks ?o } ORDER BY ?s
endef

define WARMUP_QUERY_5
SELECT ?s ?o WHERE { ?s wdt:P279+ ?o } ORDER BY ?s
endef

define WARMUP_QUERY_6
SELECT ?s ?o WHERE { ?s wdt:P279+ ?o } ORDER BY ?s
endef

define WARMUP_QUERY_7
SELECT ?s ?o WHERE { ?s wdt:P31 ?o } ORDER BY ?s
endef

define WARMUP_QUERY_8
SELECT ?s ?o WHERE { ?s wdt:P31 ?o } ORDER BY ?o
endef

define WARMUP_QUERY_9
SELECT ?s ?o WHERE { ?s wdt:P279 ?o } ORDER BY ?s
endef

define WARMUP_QUERY_10
SELECT ?s ?o WHERE { ?s wdt:P279 ?o } ORDER BY ?o
endef

define WARMUP_QUERY_11
SELECT ?s ?o WHERE { ?s wdt:P31|wdt:P279 ?o } ORDER BY ?s
endef

define WARMUP_QUERY_12
SELECT ?s ?o WHERE { ?s wdt:P31|wdt:P279 ?o } ORDER BY ?o
endef

define ENTITY_NAME_AND_ALIAS_PATTERN
?qleverui_entity rdfs:label . BIND(?qleverui_entity AS ?alias)
endef

define ENTITY_SCORE_PATTERN
{ SELECT ?qleverui_entity (COUNT(?qleverui_tmp) AS ?count) WHERE { ?qleverui_entity wdt:P31 ?qleverui_tmp } GROUP BY ?qleverui_entity }
endef

export
