SHELL = /bin/bash

BOLD := \033[1m
DIM := \033[2m
RESET := \033[0m

DATA_DIR = /local/data/entity-linking/

WIKIPEDIA_DUMP_FILES_DIR = ${DATA_DIR}wikipedia_dump_files/
WIKI_DUMP = ${WIKIPEDIA_DUMP_FILES_DIR}enwiki-latest-pages-articles-multistream.xml.bz2
EXTRACTED_WIKI_DUMP = ${WIKIPEDIA_DUMP_FILES_DIR}enwiki-latest-articles-extracted.jsonl
LINKED_WIKI_ARTICLES = ${WIKIPEDIA_DUMP_FILES_DIR}enwiki-latest-articles-linked.jsonl

# Variables for downloading wikidata files
WIKIDATA_MAPPINGS_DIR = ${DATA_DIR}wikidata_mappings/
API_WIKIDATA = https://qlever.cs.uni-freiburg.de/api/wikidata
# Note that the query names are also used for generating the file name by
# casting the query name to lowercase and appending .tsv
DATA_QUERY_NAMES = QID_TO_DEMONYM QID_TO_LANGUAGE QUANTITY DATETIME QID_TO_LABEL QID_TO_GENDER QID_TO_GIVEN_NAME QID_TO_SITELINK WIKIDATA_ENTITIES QID_TO_WIKIPEDIA_URL QID_TO_P31 QID_TO_P279
BATCH_SIZE = 10000000
NUM_LINKER_THREADS = 8


config:
	@echo
	@echo "Basic configuration variables:"
	@echo
	@for VAR in DATA_DIR WIKIPEDIA_DUMP_FILES_DIR WIKI_DUMP EXTRACTED_WIKI_DUMP LINKED_WIKI_ARTICLES \
	    WIKIDATA_MAPPINGS_DIR API_WIKIDATA DATA_QUERY_NAMES BATCH_SIZE; do \
	  printf "%-30s = %s\n" "$$VAR" "$${!VAR}"; done
	@echo
	@printf "All targets: "
	@grep "^[A-Za-z._]\+:" $(lastword $(MAKEFILE_LIST)) | sed 's/://' | paste -sd" "
	@echo
	@echo "If you're starting from scratch and do not have any of the data files available, run"
	@echo "	make setup"
	@echo "This will download a Wikipedia dump, extract the articles, split the dump into"
	@echo "training, development and test set, download all necessary Wikidata mappings"
	@echo "and compute all necessary Wikipedia mappings."
	@echo

setup: download_wiki extract_wiki split_wiki getmappings

# Download Wikipedia dump only if it does not exist already at the specified location.
download_wiki:
	@if ls ${WIKI_DUMP} 1> /dev/null 2>&1; then echo -e "\033[31mWikipedia dump already exists at ${WIKI_DUMP} . Delete or rename it first. Dump not downloaded.\033[0m"; echo; else \
	  wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles-multistream.xml.bz2 -O ${WIKI_DUMP}; \
	fi

# Extract Wikipedia dump only if it does not exist already at the specified location.
extract_wiki:
	@if ls ${EXTRACTED_WIKI_DUMP} 1> /dev/null 2>&1; then echo -e "\033[31mExtracted Wikipedia dump already exists at ${EXTRACTED_WIKI_DUMP} . Delete or rename it first. Dump not extracted.\033[0m"; echo; else \
	  python3 wiki_extractor/WikiExtractor.py --links --bold --json --output_file ${EXTRACTED_WIKI_DUMP} ${WIKI_DUMP}; \
	fi

split_wiki:
	python3 split_dataset.py

# Link Wikipedia dump only if it does not exist already at the specified location.
link_wiki:
	@if ls ${LINKED_WIKI_ARTICLES} 1> /dev/null 2>&1; then echo -e "\033[Linked Wikipedia dump already exists at ${LINKED_WIKI_ARTICLES} . Delete or rename it first. Dump not linked.\033[0m"; echo; else \
	  python3 link_entities.py ${EXTRACTED_WIKI_DUMP} ${LINKED_WIKI_ARTICLES} popular_entities 15 -ll link-text-linker -coref entity -m ${NUM_LINKER_THREADS}; \
	fi

getmappings: get_wikidata_mappings get_wikipedia_mappings get_relevant_types_mapping

# Get data for queries from $(DATA_QUERY_VARABLES) via $(API_WIKIDATA) and write to tsv files.
get_wikidata_mappings:
	@echo
	@echo "[get_wikidata_mappings] Get data for given queries in batches."
	@echo
	@echo "DATA_QUERY_NAMES = $(DATA_QUERY_NAMES)"
	for QUERY_NAME in $(DATA_QUERY_NAMES); do echo; \
	  echo $${QUERY_NAME}; \
	  LOWER_QUERY_NAME=$$(echo $${QUERY_NAME} | tr '[:upper:]' '[:lower:]'); \
	  $(MAKE) -sB API=$${API_WIKIDATA} QUERY_VARIABLE=$${QUERY_NAME}_QUERY OUTFILE=$${WIKIDATA_MAPPINGS_DIR}$${LOWER_QUERY_NAME}.tsv query.batched; done
	@echo

# These files are only needed for our coref resolver. Data generation takes several hours.
# If the coref resolver is not needed, skip this step.
get_relevant_types_mapping:
	@echo
	@echo "[get_relevant_types_mapping] Get mapping from QID to relevant types needed only for our own coref resolver."
	@echo "This can take several hours (< 6h). If the coref resolver is not needed you can skip this step."
	@echo
	python3 create_all_types_mapping.py
	python3 create_relevant_types_mapping.py

get_wikipedia_mappings:
	@echo
	@echo "[get_wikipedia_mappings] Extract mappings from Wikipedia."
	@echo
	python3 extract_akronyms.py
	python3 extract_abstracts.py
	python3 get_link_frequencies.py
	python3 extract_redirects.py ${WIKI_DUMP}
	python3 extract_title_synonyms.py
	python3 count_unigrams.py
	python3 get_wikipedia_id_to_title_mapping.py

# Get result for $(QUERY) in batches of size $(BATCH_SIZE), using query: target
query.batched:
	@echo "API = $(API)"
	@echo "OUTFILE = $(OUTFILE)"
	@true > $(OUTFILE)
	@echo "$$PREFIXES $${${QUERY_VARIABLE}}"
	@RESULT_SIZE=$$($(MAKE) -s QUERY=$${QUERY_VARIABLE} count); \
	echo "Result size = $$(echo $$RESULT_SIZE | numfmt --grouping)"; \
	for OFFSET in `seq 0 $$BATCH_SIZE $$RESULT_SIZE`; do \
	  echo "LIMIT $$BATCH_SIZE OFFSET $$OFFSET"; \
	  $(MAKE) -s QUERY=$${QUERY_VARIABLE} SUFFIX="LIMIT $$BATCH_SIZE OFFSET $$OFFSET" query; \
	done
	@echo "First line and last line of $(OUTFILE) are:"
	@head -1 $(OUTFILE) && tail -1 $(OUTFILE)

# Get results for $(QUERY), convert to tsv and append to $(OUTFILE)
#
# Short descriptions of what the 3 sed lines do:
# 1) Replace wikidata entity URIs by the QID
# 2) Replace "<string>"@en for string literals by just <string>
# 3) Replace integer literals by just the integer
# 4) Remove the <> around wikipedia urls
query:
	@curl -Gs $(API) \
	    --data-urlencode "query=$$PREFIXES $${${QUERY}} $${SUFFIX}" \
	    --data-urlencode "action=tsv_export" \
	    | sed -r 's|<http://www\.wikidata\.org/entity/([QP][0-9]+)>|\1|g' \
	    | sed -r 's|"([^\t"]*)"@en|\1|g' \
	    | sed -r 's|"([0-9][0-9]*)"\^\^<http://www\.w3\.org/2001/XMLSchema#int>|\1|g' \
	    | sed -r 's|<(http[s]*://[^\t ]*)>|\1|g' \
	    >> $(OUTFILE)

# Get result size for $(QUERY), without downloading anything of the result yet
count:
	curl -Gs $(API) \
	    --data-urlencode "query=$$PREFIXES $${${QUERY}} LIMIT 0" \
	    --data-urlencode "send=0" \
	    | grep resultsize | head -1 | sed 's/[^0-9]//g'

evaluate_own_system:
	python3 link_benchmark_entities.py evaluated_own.jsonl explosion data/linker-1M/nlp --link_linker link-text-linker -coref entity
	python3 evaluate_linked_entities.py evaluated_own.jsonl

evaluate_tagme:
	python3 link_benchmark_entities.py evaluated_tagme.jsonl tagme 0.2
	python3 evaluate_linked_entities.py evaluated_tagme.jsonl

evaluate_baseline:
	python3 link_benchmark_entities.py evaluated_baseline.jsonl baseline links-all
	python3 evaluate_linked_entities.py evaluated_baseline.jsonl

define PREFIXES
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
endef

define QID_TO_DEMONYM_QUERY
SELECT ?s ?d WHERE{
  ?s wdt:P1549 ?d .
  FILTER (LANG(?d) = "en") .
}
endef

define QID_TO_LANGUAGE_QUERY
SELECT DISTINCT ?s ?l WHERE {
  ?s wdt:P31/wdt:P279* wd:Q34770 .
  ?s @en@rdfs:label ?l .
}
endef

define QUANTITY_QUERY
SELECT DISTINCT ?real_number WHERE {
  ?real_number wdt:P31/wdt:P279* wd:Q12916
}
endef

define DATETIME_QUERY
SELECT DISTINCT ?point_in_time WHERE {
  ?point_in_time wdt:P31/wdt:P279* wd:Q186408
}
endef

# Retrieves only items with an instance-of*/subclass-of* path to "entity"
define QID_TO_LABEL_QUERY
SELECT DISTINCT ?item ?label WHERE {
  ?item @en@rdfs:label ?label
}
endef

define QID_TO_GENDER_QUERY
SELECT ?s ?ol WHERE {
  ?s wdt:P21 ?o .
  ?o @en@rdfs:label ?ol .
}
endef

define QID_TO_GIVEN_NAME_QUERY
SELECT DISTINCT ?s ?sl WHERE {
  ?s wdt:P31 wd:Q5 .
  ?s @en@rdfs:label ?sl .
}
endef

define QID_TO_SITELINK_QUERY
SELECT ?s ?o WHERE {
  ?sn schema:about ?s .
  ?sn wikibase:sitelinks ?o
}
endef

define WIKIDATA_ENTITIES_QUERY
SELECT ?name ?score ?description ?wikipedia_url ?wikidata_id (GROUP_CONCAT(?synonym; SEPARATOR=";") AS ?synonyms) ?image_url WHERE {
   ?wikipedia_url schema:about ?wikidata_id .
   ?wikipedia_url schema:isPartOf <https://en.wikipedia.org/> .
   ?wikidata_id @en@rdfs:label ?name .
   ?wikidata_id @en@schema:description ?description .
   ?wikidata_id ^schema:about/wikibase:sitelinks ?score .
   OPTIONAL { ?wikidata_id @en@skos:altLabel ?synonym }
   OPTIONAL { ?wikidata_id wdt:P18 ?image_url }
}
GROUP BY ?name ?score ?description ?wikipedia_url ?wikidata_id ?image_url
ORDER BY DESC(?score)
endef

define QID_TO_WIKIPEDIA_URL_QUERY
SELECT ?qid ?url WHERE {
   ?url schema:about ?qid .
   ?url schema:isPartOf <https://en.wikipedia.org/>
}
endef

define QID_TO_P31_QUERY
SELECT ?item ?type WHERE {
    ?item wdt:P31 ?type .
}
endef

define QID_TO_P279_QUERY
SELECT ?item ?type WHERE {
    ?item wdt:P279 ?type .
}
endef

export
