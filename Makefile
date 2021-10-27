SHELL = /bin/bash

BOLD := \033[1m
DIM := \033[2m
RESET := \033[0m

DATA_DIR = "/nfs/students/matthias-hertel/wiki_entity_linker/"

WIKIPEDIA_DUMP_FILES_DIR = ${DATA_DIR}"wikipedia_dump_files/"
WIKI_DUMP = ${WIKIPEDIA_DUMP_FILES_DIR}"enwiki-latest-pages-articles-multistream.xml.bz2"
EXTRACTED_WIKI_DUMP = ${WIKIPEDIA_DUMP_FILES_DIR}"enwiki-latest-articles-extracted.jsonl"
LINKED_WIKI_ARTICLES = ${WIKIPEDIA_DUMP_FILES_DIR}"enwiki-latest-articles-linked.jsonl"

# Variables for downloading wikidata files
WIKIDATA_MAPPINGS_DIR = ${DATA_DIR}"wikidata_mappings/"
API_WIKIDATA = https://qlever.cs.uni-freiburg.de/api/wikidata
DATA_QUERY_NAMES = DEMONYM LANGUAGE QUANTITY DATETIME LABEL GENDER NAME SITELINK WIKIPEDIA_ENTITIES_INFO WIKIPEDIA_URL
BATCH_SIZE = 10000000

help:
	@echo "${BOLD}wiki_all:${RESET}"
	@echo "		Download, extract and link an entire Wikipedia Dump."
	@echo "${BOLD}evaluate_own_system:${RESET}"
	@echo "		Evaluate our own entity linking system consisting of link-text-linker, explosion linker and entity coreference resolution."
	@echo "		The results are printed to stdout and the evaluation cases written to 'evaluated_own.cases'."
	@echo "		time to run: ~ 5 min | required RAM: ~ 24GB${RESET}"
	@echo "${BOLD}evaluate_tagme:${RESET}"
	@echo "		Evaluate Tagme."
	@echo "		The results are printed to stdout and the evaluation cases written to 'evaluated_tagme.cases'."
	@echo "		time to run: ~ 3 min | required RAM: ~ 8GB${RESET}"
	@echo "${BOLD}evaluate_baseline:${RESET}"
	@echo "		Evaluate Baseline system."
	@echo "		The results are printed to stdout and the evaluation cases written to 'evaluated_baseline.cases'."
	@echo "		time to run: ~ 6 min | required RAM: ~ 18GB${RESET}"

evaluate_own_system:
	python3 link_benchmark_entities.py evaluated_own.jsonl explosion data/linker-1M/nlp --link_linker link-text-linker -coref entity
	python3 evaluate_linked_entities.py evaluated_own.jsonl

evaluate_tagme:
	python3 link_benchmark_entities.py evaluated_tagme.jsonl tagme 0.2
	python3 evaluate_linked_entities.py evaluated_tagme.jsonl

evaluate_baseline:
	python3 link_benchmark_entities.py evaluated_baseline.jsonl baseline links-all
	python3 evaluate_linked_entities.py evaluated_baseline.jsonl

wiki_all: download_wiki extract_wiki link_wiki

download_wiki:
	wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles-multistream.xml.bz2

extract_wiki:
	python3 wiki_extractor/WikiExtractor.py --links --bold --json --output_file ${EXTRACTED_WIKI_DUMP} ${WIKI_DUMP}

split_wiki:
	python3 split_datasets.py

link_wiki:
	python3 link_entities.py ${EXTRACTED_WIKI_DUMP} ${LINKED_WIKI_ARTICLES} popular_entities 15 -ll link-text-linker -coref entity

setup: download_wiki extract_wiki split_wiki getdata

getdata: get_wikidata_mappings get_wikipedia_mappings

# Get data for queries from $(DATA_QUERY_VARABLES) via $(API_WIKIDATA) and write to tsv files.
get_wikidata_mappings:
	@echo
	@echo "[getdata] Get data for given queries in batches"
	@echo
	@echo "DATA_QUERY_NAMES = $(DATA_QUERY_NAMES)"
	for QUERY_NAME in $(DATA_QUERY_NAMES); do echo; \
	  echo $${QUERY_NAME}; \
	  $(MAKE) -sB API=$${API_WIKIDATA} QUERY_VARIABLE=$${QUERY_NAME}_QUERY OUTFILE=$${WIKIDATA_MAPPINGS_DIR}$${QUERY_NAME}.tsv query.batched; done
	@echo

get_wikipedia_mappings:
	python3 extract_akronyms.py
	python3 extract_abstracts.py
	python3 get_link_frequencies.py
	python3 extract_redirects.py ${WIKI_DUMP}
	python3 extract_title_synonyms.py
	python3 count_unigrams.py
	python3 get_wikipedia_id_to_title_mapping.py

# Get result for $(QUERY) in batches of size $(BATCH_SIZE), using query: target
query.batched:
	echo "API = $(API)"
	echo "OUTFILE = $(OUTFILE)"
	$(info $(PREFIXES))
	$(info $($(QUERY_VARIABLE)))
	@true > $(OUTFILE)
	@RESULT_SIZE=$$($(MAKE) -s QUERY="$(shell echo ${$(QUERY_VARIABLE)})" count); \
	echo "Result size = $$(echo $$RESULT_SIZE | numfmt --grouping)"; \
	for OFFSET in `seq 0 $$BATCH_SIZE $$RESULT_SIZE`; do \
	  echo "LIMIT $$BATCH_SIZE OFFSET $$OFFSET"; \
	  $(MAKE) -s QUERY="$(shell echo ${$(QUERY_VARIABLE)}) LIMIT $$BATCH_SIZE OFFSET $$OFFSET" query; \
	  echo "Query: $(shell echo ${$(QUERY_VARIABLE)})"; \
	done
	@echo "First line and last line of $(OUTFILE) are:"
	@head -1 $(OUTFILE) && tail -1 $(OUTFILE)

# Get results for $(QUERY), convert to tsv and append to $(OUTFILE)
#
# Short descriptions of what the 3 sed lines do:
# 1) Replace wikidata entity URIs by the QID
# 2) Replace "<string>"@en around string literals by just <string>
# 3) Replace integer literals by just the integer
query:
	@curl -Gs $(API) \
	    --data-urlencode "query=$$PREFIXES $(QUERY)" \
	    --data-urlencode "action=tsv_export" \
	    | sed -r 's|(.*)<http://www\.wikidata\.org/entity/([QP][0-9]+)>(.*)|\1\2\3|g' \
	    | sed -r 's|(.*)"(.*)"@en(.*)|\1\2\3|g' \
	    | sed -r 's|(.*)"([0-9][0-9]*)"\^\^<http://www\.w3\.org/2001/XMLSchema#int>(.*)|\1\2\3|g' \
	    > $(OUTFILE)

# Get result size for $(QUERY), without downloading anything of the result yet
count:
	curl -Gs $(API) \
	    --data-urlencode "query=$$PREFIXES $(QUERY) LIMIT 0" \
	    --data-urlencode "send=0" \
	    | grep resultsize | head -1 | sed 's/[^0-9]//g'

define PREFIXES
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
endef

define DEMONYM_QUERY
SELECT ?s ?d WHERE{
  ?s wdt:P1549 ?d .
  FILTER \(LANG\(?d\) = """en"""\) .
}
endef

define LANGUAGE_QUERY
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
define LABEL_QUERY
SELECT DISTINCT ?item ?label WHERE {{{{
  ?item wdt:P279 wd:Q35120 .
  ?item @en@rdfs:label ?label
} UNION {
  ?item wdt:P279 ?m . ?m wdt:P279+ wd:Q35120 .
  ?item @en@rdfs:label ?label
}} UNION {
  ?item wdt:P31 wd:Q35120 .
  ?item @en@rdfs:label ?label
}} UNION {
  ?item wdt:P31 ?m . ?m wdt:P279+ wd:Q35120 .
  ?item @en@rdfs:label ?label
} FILTER REGEX \(?item, "Q.+"\) }
endef

define GENDER_QUERY
SELECT ?s ?ol WHERE {
  ?s wdt:P21 ?o .
  ?o @en@rdfs:label ?ol .
}
endef

define NAME_QUERY
SELECT DISTINCT ?s ?sl WHERE {
  ?s wdt:P31 wd:Q5 .
  ?s @en@rdfs:label ?sl .
}
endef

define SITELINK_QUERY
SELECT ?s ?o WHERE {
  ?sn schema:about ?s .
  ?sn wikibase:sitelinks ?o
}
endef

define WIKIPEDIA_ENTITIES_INFO_QUERY
SELECT ?name ?score ?description ?wikipedia_url ?wikidata_id \(GROUP_CONCAT\(?synonym\; SEPARATOR=";"\) AS ?synonyms\) ?image_url WHERE {
   ?wikipedia_url schema:about ?wikidata_id .
   ?wikipedia_url schema:isPartOf \<https://en.wikipedia.org/\> .
   ?wikidata_id @en@rdfs:label ?name .
   ?wikidata_id @en@schema:description ?description .
   ?wikidata_id ^schema:about/wikibase:sitelinks ?score .
   OPTIONAL { ?wikidata_id @en@skos:altLabel ?synonym }
   OPTIONAL { ?wikidata_id wdt:P18 ?image_url }
}
GROUP BY ?name ?score ?description ?wikipedia_url ?wikidata_id ?image_url
ORDER BY DESC\(?score\)
endef

define WIKIPEDIA_URL_QUERY
SELECT ?qid ?url WHERE {
   ?url schema:about ?qid .
   ?url schema:isPartOf \<https://en.wikipedia.org/\>
}
endef

export
