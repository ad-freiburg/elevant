SHELL = /bin/bash

BOLD := \033[1m
DIM := \033[2m
RED := \033[31m
RESET := \033[0m

DATA_DIR = /local/data/entity-linking/

WIKIPEDIA_DUMP_FILES_DIR = ${DATA_DIR}wikipedia_dump_files/
WIKI_DUMP = ${WIKIPEDIA_DUMP_FILES_DIR}enwiki-latest-pages-articles-multistream.xml.bz2
EXTRACTED_WIKI_DUMP = ${WIKIPEDIA_DUMP_FILES_DIR}enwiki-latest-extracted.jsonl
LINKED_WIKI_ARTICLES = ${WIKIPEDIA_DUMP_FILES_DIR}enwiki-latest-linked.jsonl

# Variables for downloading wikidata files
WIKIDATA_MAPPINGS_DIR = ${DATA_DIR}wikidata_mappings/
WIKIDATA_SPARQL_ENDPOINT = https://qlever.cs.uni-freiburg.de/api/wikidata
# Note that the query names are also used for generating the file name by
# casting the query name to lowercase and appending .tsv
DATA_QUERY_NAMES = QID_TO_DEMONYM QID_TO_LANGUAGE QUANTITY DATETIME QID_TO_LABEL QID_TO_GENDER QID_TO_GIVEN_NAME QID_TO_SITELINK WIKIDATA_ENTITIES QID_TO_WIKIPEDIA_URL QID_TO_P31 QID_TO_P279
BATCH_SIZE = 10000000
NUM_LINKER_PROCESSES = 1

# Variables for benchmark linking and evaluation
EVALUATION_RESULTS_DIR = evaluation_results/
# Adjust if you only want to link or evaluate certain benchmarks
BENCHMARK_NAMES = wiki-ex newscrawl conll-test conll-dev msnbc ace msnbc-original ace-original kore50
# Adjust if you only want to link with certain linking systems.
# The script arguments for a linking system can be adjusted in the link_benchmark target if needed.
LINKING_SYSTEMS = ambiverse baseline explosion neural_el popular_entities pos_prior spacy spacy_wikipedia tagme wikifier
# Edit if you only want to evaluate a linking system that matches a certain prefix.
EVALUATE_LINKING_SYSTEM_PREFIX =

DOCKER_CMD = docker


config:
	@echo
	@echo "Basic configuration variables:"
	@echo
	@for VAR in DATA_DIR WIKIPEDIA_DUMP_FILES_DIR WIKI_DUMP EXTRACTED_WIKI_DUMP LINKED_WIKI_ARTICLES \
	    WIKIDATA_MAPPINGS_DIR WIKIDATA_SPARQL_ENDPOINT DATA_QUERY_NAMES BATCH_SIZE; do \
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

link_benchmarks:
	@echo
	@echo "[link_benchmarks] Link given benchmarks with given systems"
	@echo
	@echo "BENCHMARK_NAMES = $(BENCHMARK_NAMES)"
	@echo "LINKING_SYSTEMS = $(LINKING_SYSTEMS)"
	for BENCHMARK_NAME in $(BENCHMARK_NAMES); do echo; \
	  $(MAKE) -sB BENCHMARK=$${BENCHMARK_NAME} link_benchmark; done
	@echo

link_benchmark:
	for SYSTEM in $(LINKING_SYSTEMS); do \
	  echo "BENCHMARK: $${BENCHMARK}"; \
	  echo "LINKING SYSTEM: $${SYSTEM}"; \
	  RESULT_NAME=$${SYSTEM}; \
	  if [ $${SYSTEM} == "ambiverse" ]; then \
	    ARGUMENTS=/nfs/students/natalie-prange/ambiverse_data/results/benchmark_$${BENCHMARK}/; \
	  elif [ $${SYSTEM} == "baseline" ]; then \
	    ARGUMENTS=links-all; \
	  elif [ $${SYSTEM} == "explosion" ]; then \
	    ARGUMENTS=/local/data/entity-linking/linker_files/explosion_linker_models/1M/; \
	  elif [ $${SYSTEM} == "neural_el" ]; then \
	    ARGUMENTS=/nfs/students/natalie-prange/neural-el-data/results/linked_articles_$${BENCHMARK}.jsonl; \
	  elif [ $${SYSTEM} == "popular_entities" ]; then \
	    ARGUMENTS="15 -ll link-text-linker -coref entity"; \
	    RESULT_NAME=$${SYSTEM}.ltl.entity; \
	  elif [ $${SYSTEM} == "pos_prior" ]; then \
	    ARGUMENTS=data/whitelist_types.txt; \
	  elif [ $${SYSTEM} == "spacy" ]; then \
	    ARGUMENTS=prior_trained; \
	    RESULT_NAME=$${SYSTEM}.prior_trained; \
	  elif [ $${SYSTEM} == "spacy_wikipedia" ]; then \
	    SYSTEM=spacy; \
	    ARGUMENTS="wikipedia -kb wikipedia"; \
	    RESULT_NAME=$${SYSTEM}.wikipedia; \
	  elif [ $${SYSTEM} == "tagme" ]; then \
	    ARGUMENTS=0.2; \
	  elif [ $${SYSTEM} == "wikifier" ]; then \
	    ARGUMENTS=/nfs/students/natalie-prange/wikifier_data/output/benchmark_$${BENCHMARK}/; \
	  else \
	    echo -e "$${DIM}No rule for linking system $${SYSTEM} found in Makefile.$${RESET}"; \
	    continue; \
	  fi; \
	  python3 link_benchmark_entities.py $${RESULT_NAME} $${SYSTEM} $${ARGUMENTS} -b $${BENCHMARK} -dir $${EVALUATION_RESULTS_DIR}; \
	done

evaluate_linked_benchmarks:
	@echo
	@echo "[evaluate_linked_benchmarks] Evaluate all linking results for all benchmarks"
	@echo
	@echo "BENCHMARK_NAMES = $(BENCHMARK_NAMES)"
	@echo "EVALUATION_RESULTS_DIR = $(EVALUATION_RESULTS_DIR)"
	@echo
	for FILENAME in ${EVALUATION_RESULTS_DIR}*/*.jsonl ; do \
	  BENCHMARK_SUFFIX=$$(echo $${FILENAME} | sed -r 's|.+\.([^\.]*)\.jsonl|\1|') ; \
	  HAS_SYSTEM_PREFIX=$$(echo $${FILENAME} | sed 's|${EVALUATE_LINKING_SYSTEM_PREFIX}||') ; \
	  if [[ "$${HAS_SYSTEM_PREFIX}" == "$${FILENAME}" ]]; then \
	    echo -e "$${DIM}Skipping $${FILENAME} because filename does not match EVALUATE_LINKING_SYSTEM_PREFIX$${RESET}"; \
	    continue; \
	  fi; \
	  echo "FILENAME = $${FILENAME}"; \
	  echo "BENCHMARK_SUFFIX = $${BENCHMARK_SUFFIX}"; \
	  if [[ " $${BENCHMARK_NAMES[*]} " =~ " $${BENCHMARK_SUFFIX} " ]]; then \
		python3 evaluate_linked_entities.py $${FILENAME} -b $${BENCHMARK_SUFFIX}; \
	  else \
	    echo -e "$${DIM}Skipping file because benchmark suffix is not in BENCHMARK_NAMES$${RESET}"; \
	  fi; \
	  echo; \
	done

setup: download_wiki extract_wiki split_wiki getmappings

# Only clone or build qlever if no qlever.master docker image exists
build_entity_types:
	@if [[ "${DOCKER_CMD}" == "wharfer"  ]] || [[ "$$(docker images -q qlever.master 2> /dev/null)" == "" ]]; then \
	  if [[ -d qlever ]]; then \
	    cd qlever; git pull --recurse-submodules; cd ..; \
	  else \
	    git clone --recursive https://github.com/ad-freiburg/qlever; \
	  fi; \
	  ${DOCKER_CMD} build -t qlever.master ./qlever; \
	else \
	  echo -e "$${BOLD}QLever docker image already exists. Using existing image.$${RESET}"; \
	fi

	cd wikidata-types; chmod 777 index; $(MAKE) -sB DOCKER_CMD=${DOCKER_CMD} WIKIDATA_SPARQL_ENDPOINT=${WIKIDATA_SPARQL_ENDPOINT} -f Makefile; cd ..
	@[ -d ${WIKIDATA_MAPPINGS_DIR} ] || mkdir ${WIKIDATA_MAPPINGS_DIR}
	mv wikidata-types/entity-types.tsv ${WIKIDATA_MAPPINGS_DIR}

download_entity_types:
	wget http://ad-research/data/entity-linking/entity-types.tsv
	@[ -d ${WIKIDATA_MAPPINGS_DIR} ] || mkdir ${WIKIDATA_MAPPINGS_DIR}
	mv entity-types.tsv ${WIKIDATA_MAPPINGS_DIR}

# Download Wikipedia dump only if it does not exist already at the specified location.
download_wiki:
	@[ -d ${WIKIPEDIA_DUMP_FILES_DIR} ] || mkdir ${WIKIPEDIA_DUMP_FILES_DIR}
	@if ls ${WIKI_DUMP} 1> /dev/null 2>&1; then echo -e "$${RED}Wikipedia dump already exists at ${WIKI_DUMP} . Delete or rename it first. Dump not downloaded.$${RESET}"; echo; else \
	  wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles-multistream.xml.bz2 -O ${WIKI_DUMP}; \
	fi

# Extract Wikipedia dump only if it does not exist already at the specified location.
extract_wiki:
	@if ls ${EXTRACTED_WIKI_DUMP} 1> /dev/null 2>&1; then echo -e "$${RED}Extracted Wikipedia dump already exists at ${EXTRACTED_WIKI_DUMP} . Delete or rename it first. Dump not extracted.$${RESET}"; echo; else \
	  python3 third_party/wiki_extractor/WikiExtractor.py --sections --links --bold --json --output_file ${EXTRACTED_WIKI_DUMP} ${WIKI_DUMP}; \
	fi

split_wiki:
	python3 split_dataset.py

# Link Wikipedia dump only if it does not exist already at the specified location.
link_wiki:
	@if ls ${LINKED_WIKI_ARTICLES} 1> /dev/null 2>&1; then echo -e "$${RED}Linked Wikipedia dump already exists at ${LINKED_WIKI_ARTICLES} . Delete or rename it first. Dump not linked.$${RESET}"; echo; else \
	  python3 link_entities.py ${EXTRACTED_WIKI_DUMP} ${LINKED_WIKI_ARTICLES} popular_entities 15 -ll link-text-linker -coref entity -m ${NUM_LINKER_PROCESSES}; \
	fi

getmappings: get_wikidata_mappings build_wikipedia_mappings build_coreference_types_mapping

build_coreference_types_mapping:
	@echo
	@echo "[build_coreference_types_mapping] Get mapping from QID to coreference types needed only for our own coref resolver."
	@echo "Takes <= 30 mins. If the coref resolver is not needed you can skip this step."
	@echo
	python3 create_all_types_mapping.py  # Needs qid_to_sitelinks, qid_to_p31 and qid_to_p279
	python3 create_coreference_types_mapping.py

build_wikipedia_mappings:
	@echo
	@echo "[build_wikipedia_mappings] Build mappings from Wikipedia."
	@echo
	@[ -d ${DATA_DIR}wikipedia_mappings ] || mkdir ${DATA_DIR}wikipedia_mappings
	python3 extract_akronyms.py
	python3 extract_abstracts.py
	python3 get_link_frequencies.py
	python3 extract_redirects.py ${WIKI_DUMP}
	python3 extract_title_synonyms.py
	python3 count_unigrams.py
	python3 get_wikipedia_id_to_title_mapping.py
	python3 create_abstracts_mapping.py  # Needs redirects and qid_to_wikipedia_url.tsv

# Get data for queries from $(DATA_QUERY_VARABLES) via $(WIKIDATA_SPARQL_ENDPOINT) and write to tsv files.
get_wikidata_mappings:
	@echo
	@echo "[get_wikidata_mappings] Get data for given queries in batches."
	@echo
	@echo "DATA_QUERY_NAMES = $(DATA_QUERY_NAMES)"
	@[ -d ${WIKIDATA_MAPPINGS_DIR} ] || mkdir ${WIKIDATA_MAPPINGS_DIR}
	for QUERY_NAME in $(DATA_QUERY_NAMES); do echo; \
	  echo $${QUERY_NAME}; \
	  LOWER_QUERY_NAME=$$(echo $${QUERY_NAME} | tr '[:upper:]' '[:lower:]'); \
	  $(MAKE) -sB API=$${WIKIDATA_SPARQL_ENDPOINT} QUERY_VARIABLE=$${QUERY_NAME}_QUERY OUTFILE=$${WIKIDATA_MAPPINGS_DIR}$${LOWER_QUERY_NAME}.tsv query; done
	@echo

# Get results for $(QUERY), convert to tsv and append to $(OUTFILE)
#
# Short descriptions of what the 3 sed lines do:
# 0) Drop lines with Wikidata properties or lexemes
# 1) Replace wikidata entity URIs by the QID
# 2) Replace "<string>"@en for string literals by just <string>
# 3) Replace integer literals by just the integer
# 4) Remove the <> around wikipedia urls
query:
	@echo "API = ${API}"
	@echo "OUTFILE = ${OUTFILE}"
	@echo "$$PREFIXES $${${QUERY_VARIABLE}}"
	@curl -Gs ${API} -H "Accept: text/tab-separated-values"\
	    --data-urlencode "query=$$PREFIXES $${${QUERY_VARIABLE}} LIMIT 200000000" \
	    | sed -r '/<http:\/\/www\.wikidata\.org\/entity\/[LP][^>]*>/d' \
	    | sed -r 's|<http://www\.wikidata\.org/entity/([Q][0-9]+)>|\1|g' \
	    | sed -r 's|"([^\t"]*)"@en|\1|g' \
	    | sed -r 's|"([0-9][0-9]*)"\^\^<http://www\.w3\.org/2001/XMLSchema#int>|\1|g' \
	    | sed -r 's|<(http[s]*://[^\t ]*)>|\1|g' \
	    > ${OUTFILE}
	@echo "Number of lines in ${OUTFILE}:"
	@wc -l ${OUTFILE} | cut -f 1 -d " "
	@echo "First and last line:"
	@head -1 ${OUTFILE} && tail -1 ${OUTFILE}

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
SELECT ?name ?score ?wikidata_id (GROUP_CONCAT(?synonym; SEPARATOR=";") AS ?synonyms) WHERE {
   ?wikipedia_url schema:about ?wikidata_id .
   ?wikipedia_url schema:isPartOf <https://en.wikipedia.org/> .
   ?wikidata_id @en@rdfs:label ?name .
   ?wikidata_id ^schema:about/wikibase:sitelinks ?score .
   OPTIONAL { ?wikidata_id @en@skos:altLabel ?synonym }
}
GROUP BY ?name ?score ?wikipedia_url ?wikidata_id
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
