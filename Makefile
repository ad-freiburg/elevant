SHELL = /bin/bash

BOLD := \033[1m
DIM := \033[2m
RED := \033[31m
RESET := \033[0m

DATA_DIR = /local/data-ssd/entity-linking

WIKIPEDIA_ARTICLES_DIR = ${DATA_DIR}/wikipedia-articles/
WIKI_DUMP = ${WIKIPEDIA_ARTICLES_DIR}enwiki-latest-pages-articles-multistream.xml.bz2
EXTRACTED_WIKI_DUMP = ${WIKIPEDIA_ARTICLES_DIR}wikipedia.articles.jsonl
RESULTS_DIR = ${DATA_DIR}/results/
LINKED_WIKI_ARTICLES = ${RESULTS_DIR}wikipedia.articles.linked.jsonl

# Variables for generating wikidata mappings
WIKIDATA_MAPPINGS_DIR = ${DATA_DIR}/wikidata-mappings/
WIKIDATA_SPARQL_ENDPOINT = https://qlever.cs.uni-freiburg.de/api/wikidata
# Note that the query names are also used for generating the file name by
# casting the query name to lowercase and appending .tsv
DATA_QUERY_NAMES = QID_TO_DEMONYM QID_TO_LANGUAGE QUANTITY DATETIME QID_TO_LABEL QID_TO_GENDER QID_TO_NAME QID_TO_SITELINKS QID_TO_ALIASES QID_TO_WIKIPEDIA_URL QID_TO_P31 QID_TO_P279

# Variables for generating wikipedia mappings
WIKIPEDIA_MAPPINGS_DIR = ${DATA_DIR}/wikipedia-mappings/

# Variables for benchmark linking and evaluation
EVALUATION_RESULTS_DIR = evaluation-results/
# Adjust if you only want to link or evaluate certain benchmarks
BENCHMARK_NAMES = wiki-fair-no-coref news-fair-no-coref kore50 msnbc msnbc-updated spotlight # aida-conll-test aida-conll-dev
# Adjust if you only want to link with certain linking systems.
# The script arguments for a linking system can be adjusted in the link_benchmark target if needed.
LINKING_SYSTEMS = refined rel dbpedia-spotlight tagme baseline # spacy.wikipedia spacy.wikidata
PREDICTIONS = # neural-el ambiverse
# Edit if you only want to evaluate a linking system that matches a certain prefix.
EVALUATE_LINKING_SYSTEM_PREFIX =

# Number of processes used when linking articles (not used for linking benchmark articles)
NUM_LINKER_PROCESSES = 10

# Variables for the Evaluation Web App
WEB_APP_PORT = 8000


config:
	@echo
	@echo "Basic configuration variables:"
	@echo
	@for VAR in DATA_DIR WIKIPEDIA_ARTICLES_DIR WIKI_DUMP EXTRACTED_WIKI_DUMP LINKED_WIKI_ARTICLES \
	    WIKIDATA_MAPPINGS_DIR WIKIDATA_SPARQL_ENDPOINT DATA_QUERY_NAMES; do \
	  printf "%-30s = %s\n" "$$VAR" "$${!VAR}"; done
	@echo
	@printf "All targets: "
	@grep "^[A-Za-z._]\+:" $(lastword $(MAKEFILE_LIST)) | sed 's/://' | paste -sd" "
	@echo
	@echo "If you're starting from scratch and do not have any of the data files available, run"
	@echo "	make download_data"
	@echo "This will download a Wikipedia dump, extract the articles, split the dump into"
	@echo "training, development and test set, download all necessary Wikidata mappings"
	@echo "and compute all necessary Wikipedia mappings."
	@echo

check-data-directory:
	@if [ ! -d ${DATA_DIR} ]; then \
		echo "The directory ${DATA_DIR} does not exist."; \
		echo "Make sure you set the DATA_DIR variable correctly in the Makefile as well as the data_directory field in configs/elevant.config.json."; \
		echo "Within docker this happens automatically."; \
		false; \
	fi

link-benchmarks:
	@echo
	@echo "[link-benchmarks] Link given benchmarks with given systems"
	@echo
	@echo "BENCHMARK_NAMES = $(BENCHMARK_NAMES)"
	@echo "LINKING_SYSTEMS = $(LINKING_SYSTEMS)"
	for SYSTEM in $(LINKING_SYSTEMS); do \
	  echo; \
	  ARGUMENTS=""; \
	  RESULT_NAME=$${SYSTEM}; \
	  if [ $${SYSTEM} == "spacy.wikidata" ]; then \
	    SYSTEM=spacy; \
	    RESULT_NAME=$${SYSTEM}.wikidata; \
	    ARGUMENTS="--linker_config configs/spacy_wikidata.config.json"; \
	  elif [ $${SYSTEM} == "spacy.wikipedia" ]; then \
	    SYSTEM=spacy; \
	    RESULT_NAME=$${SYSTEM}.wikipedia; \
	  fi; \
	  echo -e "$${DIM}python3 link_benchmark.py $${RESULT_NAME} -l $${SYSTEM} -b ${BENCHMARK_NAMES} -dir ${EVALUATION_RESULTS_DIR} $${ARGUMENTS}$${RESET}"; \
	  python3 link_benchmark.py $${RESULT_NAME} -l $${SYSTEM} -b ${BENCHMARK_NAMES} -dir ${EVALUATION_RESULTS_DIR} $${ARGUMENTS}; \
	done
	@echo

convert-predictions:
	@echo
	@echo "[convert-predictions] Link given benchmarks with given systems"
	@echo
	@echo "BENCHMARK_NAMES = $(BENCHMARK_NAMES)"
	@echo "PREDICTIONS FROM = $(PREDICTIONS)"
	for BENCHMARK_NAME in $(BENCHMARK_NAMES); do echo; \
	  $(MAKE) -sB BENCHMARK=$${BENCHMARK_NAME} convert-benchmark-predictions; \
	done
	@echo

convert-benchmark-predictions:
	for PREDICTION in $(PREDICTIONS); do \
	  echo; \
	  echo "BENCHMARK: $${BENCHMARK}"; \
	  echo "PREDICTIONS FROM: $${PREDICTION}"; \
	  RESULT_NAME=$${PREDICTION}; \
	  if [ $${PREDICTION} == "ambiverse" ]; then \
	    PFILE=/nfs/students/natalie-prange/ambiverse_data/results/benchmark_$${BENCHMARK}/; \
	    PFORMAT=ambiverse; \
	    PNAME=Ambiverse; \
	  elif [ $${PREDICTION} == "neural-el" ]; then \
	    PFILE=/nfs/students/natalie-prange/neural-el-data/results/linked_articles_$${BENCHMARK}.jsonl; \
	    PFORMAT=simple-jsonl; \
	    PNAME="Neural EL"; \
	  elif [ $${PREDICTION} == "wikifier" ]; then \
	    PFILE=/nfs/students/natalie-prange/wikifier_data/output/benchmark_$${BENCHMARK}/; \
	    PFORMAT=wikifier; \
	    PNAME=Wikifier; \
	  else \
	    echo -e "$${DIM}No rule for predictions from $${PREDICTION} found in Makefile.$${RESET}"; \
	    continue; \
	  fi; \
	  python3 link_benchmark.py $${RESULT_NAME} -pfile $${PFILE} -pformat $${PFORMAT} -pname "$${PNAME}" -b $${BENCHMARK} -dir $${EVALUATION_RESULTS_DIR}; \
	done


evaluate-linking-results:
	@echo
	@echo "[evaluate-linking-results] Evaluate all linking results for all benchmarks"
	@echo
	@echo "BENCHMARK_NAMES = $(BENCHMARK_NAMES)"
	@echo "EVALUATION_RESULTS_DIR = $(EVALUATION_RESULTS_DIR)"
	@echo "EVALUATE_LINKING_SYSTEM_PREFIX = $(EVALUATE_LINKING_SYSTEM_PREFIX)"
	@echo
	for BENCHMARK in $(BENCHMARK_NAMES); do \
		echo; \
		echo -e "$${DIM}python3 evaluate.py ${EVALUATION_RESULTS_DIR}*/${EVALUATE_LINKING_SYSTEM_PREFIX}*$${BENCHMARK}.linked_articles.jsonl -b $${BENCHMARK}$${RESET}"; \
		python3 evaluate.py ${EVALUATION_RESULTS_DIR}*/${EVALUATE_LINKING_SYSTEM_PREFIX}*$${BENCHMARK}.linked_articles.jsonl -b $${BENCHMARK}; \
	done

generate-entity-types-mapping:
	@echo
	@echo "[generate-entity-types-mapping] Get data for given queries in batches."
	@echo
	docker pull adfreiburg/qlever
	rm -f wikidata-types/types.tsv
	rm wikidata-types/index/* -rf  # Remove old Wikidata-Types index to be able to build a new one
	ln -sr small-data-files/whitelist_types.tsv wikidata-types/types.tsv
	cd wikidata-types; chmod 777 index; $(MAKE) -sB WIKIDATA_SPARQL_ENDPOINT=${WIKIDATA_SPARQL_ENDPOINT} -f Makefile; cd ..
	@[ -d ${WIKIDATA_MAPPINGS_DIR} ] || mkdir ${WIKIDATA_MAPPINGS_DIR}
	mv wikidata-types/entity-types.tsv ${WIKIDATA_MAPPINGS_DIR}
	# Remove old dbm database file if it exists and is not a directory. Make apparently returns an error if [ ... ]
	# evaluates to false, therefore append || true
	[ -f ${WIKIDATA_MAPPINGS_DIR}qid_to_whitelist_types.db ] && rm -f ${WIKIDATA_MAPPINGS_DIR}qid_to_whitelist_types.db || true
	python3 scripts/create_databases.py ${WIKIDATA_MAPPINGS_DIR}entity-types.tsv -f multiple_values -o ${WIKIDATA_MAPPINGS_DIR}qid_to_whitelist_types.db

download-all: check-data-directory download-wikidata-mappings download-wikipedia-mappings download-entity-types-mapping

download-wikidata-mappings:
	@[ -d ${WIKIDATA_MAPPINGS_DIR} ] || mkdir ${WIKIDATA_MAPPINGS_DIR}
	wget https://ad-research.cs.uni-freiburg.de/data/entity-linking/wikidata_mappings.tar.gz
	tar -xvzf wikidata_mappings.tar.gz -C ${WIKIDATA_MAPPINGS_DIR}
	rm wikidata_mappings.tar.gz

download-wikipedia-mappings:
	@[ -d ${WIKIPEDIA_MAPPINGS_DIR} ] || mkdir ${WIKIPEDIA_MAPPINGS_DIR}
	wget https://ad-research.cs.uni-freiburg.de/data/entity-linking/wikipedia_mappings.tar.gz
	tar -xvzf wikipedia_mappings.tar.gz -C ${WIKIPEDIA_MAPPINGS_DIR}
	rm wikipedia_mappings.tar.gz

download-entity-types-mapping:
	@[ -d ${WIKIDATA_MAPPINGS_DIR} ] || mkdir ${WIKIDATA_MAPPINGS_DIR}
	wget https://ad-research.cs.uni-freiburg.de/data/entity-linking/qid_to_whitelist_types.tar.gz
	tar -xvzf qid_to_whitelist_types.tar.gz -C ${WIKIDATA_MAPPINGS_DIR}
	rm qid_to_whitelist_types.tar.gz

download-spacy-linking-files:
	@[ -d ${DATA_DIR}/linker-files ] || mkdir ${DATA_DIR}/linker-files
	wget https://ad-research.cs.uni-freiburg.de/data/entity-linking/spacy_linker_files.tar.gz
	tar -xvzf spacy_linker_files.tar.gz -C ${DATA_DIR}/linker-files
	rm spacy_linker_files.tar.gz


# Download Wikipedia dump only if it does not exist already at the specified location.
download-wiki:
	@[ -d ${WIKIPEDIA_ARTICLES_DIR} ] || mkdir ${WIKIPEDIA_ARTICLES_DIR}
	@if ls ${WIKI_DUMP} 1> /dev/null 2>&1; then echo -e "$${RED}Wikipedia dump already exists at ${WIKI_DUMP} . Delete or rename it if you want to download a new dump. Dump not downloaded.$${RESET}"; echo; else \
	  wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles-multistream.xml.bz2 -O ${WIKI_DUMP}; \
	fi

# Extract Wikipedia dump only if it does not exist already at the specified location.
extract-wiki:
	@if ls ${EXTRACTED_WIKI_DUMP} 1> /dev/null 2>&1; then echo -e "$${RED}Extracted Wikipedia dump already exists at ${EXTRACTED_WIKI_DUMP} . Delete or rename it if you want to extract another dump. Dump not extracted.$${RESET}"; echo; else \
	  python3 third-party/wiki-extractor/WikiExtractor.py --sections --links --bold --json --output_file ${EXTRACTED_WIKI_DUMP} ${WIKI_DUMP}; \
	fi

split-wiki:
	python3 scripts/split_dataset.py

# Link Wikipedia dump only if it does not exist already at the specified location.
link-wiki:
	@[ -d ${RESULTS_DIR} ] || mkdir ${RESULTS_DIR}
	@if ls ${LINKED_WIKI_ARTICLES} 1> /dev/null 2>&1; then echo -e "$${RED}Linked Wikipedia dump already exists at ${LINKED_WIKI_ARTICLES} . Delete or rename it if you want to link another dump. Dump not linked.$${RESET}"; echo; else \
	  python3 link_text.py ${EXTRACTED_WIKI_DUMP} ${LINKED_WIKI_ARTICLES} -l popular-entities -coref kb-coref -m ${NUM_LINKER_PROCESSES}; \
	fi

generate-all: check-data-directory generate-entity-types-mapping generate-wikidata-mappings generate-wikipedia-mappings

generate-wikipedia-mappings: download-wiki extract-wiki split-wiki
	@echo
	@echo "[generate-wikipedia-mappings] Build mappings from Wikipedia."
	@echo
	@[ -d ${WIKIPEDIA_MAPPINGS_DIR} ] || mkdir ${WIKIPEDIA_MAPPINGS_DIR}
	python3 scripts/extract_akronyms.py
	python3 scripts/extract_redirects.py ${WIKI_DUMP}
	[ -f ${WIKIPEDIA_MAPPINGS_DIR}redirects.db ] && rm -f ${WIKIPEDIA_MAPPINGS_DIR}redirects.db || true
	python3 scripts/create_databases.py ${WIKIPEDIA_MAPPINGS_DIR}redirects.pkl
	python3 scripts/get_link_frequencies.py  # Needs redirects and qid_to_wikipedia_url.db
	[ -f ${WIKIPEDIA_MAPPINGS_DIR}hyperlink_to_most_popular_candidates.db ] && rm -f ${WIKIPEDIA_MAPPINGS_DIR}hyperlink_to_most_popular_candidates.db || true
	python3 scripts/create_databases.py ${WIKIPEDIA_MAPPINGS_DIR}hyperlink_frequencies.pkl -o ${WIKIPEDIA_MAPPINGS_DIR}hyperlink_to_most_popular_candidates.db  --most_popular_candidates
	python3 scripts/extract_title_synonyms.py
	python3 scripts/count_unigrams.py
	python3 scripts/get_wikipedia_id_to_title_mapping.py
	python3 scripts/create_abstracts_mapping.py  # Needs redirects and qid_to_wikipedia_url.db

generate-wikidata-mappings: get-qlever-mappings generate-databases generate-coreference-type-mappings

# Get data for queries from $(DATA_QUERY_VARABLES) via $(WIKIDATA_SPARQL_ENDPOINT) and write to tsv files.
get-qlever-mappings:
	@echo
	@echo "[get-qlever-mappings] Get data for given queries in batches."
	@echo
	@echo "DATA_QUERY_NAMES = $(DATA_QUERY_NAMES)"
	@[ -d ${WIKIDATA_MAPPINGS_DIR} ] || mkdir ${WIKIDATA_MAPPINGS_DIR}
	for QUERY_NAME in $(DATA_QUERY_NAMES); do echo; \
	  echo $${QUERY_NAME}; \
	  LOWER_QUERY_NAME=$$(echo $${QUERY_NAME} | tr '[:upper:]' '[:lower:]'); \
	  $(MAKE) -sB API=$${WIKIDATA_SPARQL_ENDPOINT} QUERY_VARIABLE=$${QUERY_NAME}_QUERY OUTFILE=$${WIKIDATA_MAPPINGS_DIR}$${LOWER_QUERY_NAME}.tsv query; done
	@echo

generate-coreference-type-mappings:
	@echo
	@echo "Get mapping from QID to coreference types needed only for our own coref resolver."
	@echo "Takes ca. 1h. If the coref resolver is not needed you can skip this step."
	@echo
	python3 scripts/create_all_types_mapping.py  # Needs qid_to_sitelinks, qid_to_p31 and qid_to_p279
	python3 scripts/create_coreference_types_mapping.py
	@echo

generate-databases:
	@echo
	@echo "[generate-databases] Build databases from large Wikidata mappings."
	@echo
	[ -f ${WIKIDATA_MAPPINGS_DIR}wikipedia_name_to_qid.db ] && rm -f ${WIKIDATA_MAPPINGS_DIR}wikipedia_name_to_qid.db || true
	python3 scripts/create_databases.py ${WIKIDATA_MAPPINGS_DIR}qid_to_wikipedia_url.tsv -i -m name_from_url -o ${WIKIDATA_MAPPINGS_DIR}wikipedia_name_to_qid.db
	[ -f ${WIKIDATA_MAPPINGS_DIR}qid_to_sitelinks.db ] && rm -f ${WIKIDATA_MAPPINGS_DIR}qid_to_sitelinks.db || true
	python3 scripts/create_databases.py ${WIKIDATA_MAPPINGS_DIR}qid_to_sitelinks.tsv
	[ -f ${WIKIDATA_MAPPINGS_DIR}qid_to_label.db ] && rm -f ${WIKIDATA_MAPPINGS_DIR}qid_to_label.db || true
	python3 scripts/create_databases.py ${WIKIDATA_MAPPINGS_DIR}qid_to_label.tsv
	[ -f ${WIKIDATA_MAPPINGS_DIR}label_to_qids.db ] && rm -f ${WIKIDATA_MAPPINGS_DIR}label_to_qids.db || true
	python3 scripts/create_databases.py ${WIKIDATA_MAPPINGS_DIR}qid_to_label.tsv -i -f multiple_values -o ${WIKIDATA_MAPPINGS_DIR}label_to_qids.db
	[ -f ${WIKIDATA_MAPPINGS_DIR}alias_to_qids.db ] && rm -f ${WIKIDATA_MAPPINGS_DIR}alias_to_qids.db || true
	python3 scripts/create_databases.py ${WIKIDATA_MAPPINGS_DIR}qid_to_aliases.tsv -i -f multiple_values_semicolon_separated -o ${WIKIDATA_MAPPINGS_DIR}alias_to_qids.db
	[ -f ${WIKIDATA_MAPPINGS_DIR}qid_to_aliases.db ] && rm -f ${WIKIDATA_MAPPINGS_DIR}qid_to_aliases.db || true
	python3 scripts/create_databases.py ${WIKIDATA_MAPPINGS_DIR}qid_to_aliases.tsv -f multiple_values_semicolon_separated

cleanup:
	rm ${WIKIDATA_MAPPINGS_DIR}qid_to_wikipedia_url.tsv -f
	rm ${WIKIDATA_MAPPINGS_DIR}qid_to_sitelinks.tsv -f
	rm ${WIKIDATA_MAPPINGS_DIR}qid_to_label.tsv -f
	rm ${WIKIDATA_MAPPINGS_DIR}qid_to_aliases.tsv -f
	rm ${WIKIDATA_MAPPINGS_DIR}entity-types.tsv -f
	rm ${WIKIDATA_MAPPINGS_DIR}qid_to_p279.tsv -f
	rm ${WIKIDATA_MAPPINGS_DIR}qid_to_p31.tsv -f
	rm ${WIKIDATA_MAPPINGS_DIR}qid_to_all_types.tsv -f
	rm ${WIKIPEDIA_MAPPINGS_DIR}redirects.pkl -f

# Get results for $(QUERY), convert to tsv and append to $(OUTFILE)
#
# Short descriptions of what the 3 sed lines do:
# 0) Replace wikidata entity URIs by the QID
# 1) Drop lines that don't start with Q
#    (e.g. Wikidata properties or lexemes or the first line of the file with column titles that start with "?")
# 2) Replace "<string>"@en for string literals by just <string>
# 3) Replace integer literals by just the integer
# 4) Remove the <> around wikipedia urls
query:
	@echo "API = ${API}"
	@echo "OUTFILE = ${OUTFILE}"
	@echo "$$PREFIXES $${${QUERY_VARIABLE}}"
	@curl -Gs ${API} -H "Accept: text/tab-separated-values"\
	    --data-urlencode "query=$$PREFIXES $${${QUERY_VARIABLE}} LIMIT 200000000" \
	     > ${DATA_DIR}/tmp.tsv
	@cat ${DATA_DIR}/tmp.tsv \
	    | sed -r 's|<http://www\.wikidata\.org/entity/([Q][0-9]+)>|\1|g' \
	    | sed -r '/^[^Q]/d' \
	    | sed -r 's|"([^\t"]*)"@en|\1|g' \
	    | sed -r 's|"([0-9][0-9]*)"\^\^<http://www\.w3\.org/2001/XMLSchema#int>|\1|g' \
	    | sed -r 's|<(http[s]*://[^\t ]*)>|\1|g' \
	    > ${OUTFILE}
	@echo "Number of lines in ${OUTFILE}:"
	@wc -l ${OUTFILE} | cut -f 1 -d " "
	@echo "First and last line:"
	@head -1 ${OUTFILE} && tail -1 ${OUTFILE}
	@rm -f ${DATA_DIR}/tmp.tsv

# Start the evaluation webapp.
# If necessary create the symbolic links to the evaluation results and the benchmarks directory first.
start-webapp:
	@echo
	@echo "[start-webapp] Start the web app."
	@echo
	@[ -L evaluation-webapp/evaluation-results ] || ln -sr ${EVALUATION_RESULTS_DIR} evaluation-webapp/evaluation-results
	@[ -L evaluation-webapp/benchmarks ] || ln -sr benchmarks/ evaluation-webapp/benchmarks
	@[ -L evaluation-webapp/whitelist_types.tsv ] || ln -sr small-data-files/whitelist_types.tsv evaluation-webapp/whitelist_types.tsv
	python3 -m http.server --directory evaluation-webapp ${WEB_APP_PORT}

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

define QID_TO_NAME_QUERY
SELECT DISTINCT ?s ?sl WHERE {
  {
    ?s wdt:P31 wd:Q5 .
    ?s @en@rdfs:label ?sl .
  } UNION {
    ?s wdt:P31/wdt:P279* wd:Q95074 .
    ?s @en@rdfs:label ?sl .
  }
}
endef

define QID_TO_SITELINKS_QUERY
SELECT ?s ?o WHERE {
  ?sn schema:about ?s .
  ?sn wikibase:sitelinks ?o
  FILTER(?o > 0)
} ORDER BY DESC(?o)
endef

define QID_TO_ALIASES_QUERY
SELECT ?wikidata_id (GROUP_CONCAT(?synonym; SEPARATOR=";") AS ?synonyms) WHERE {
   ?wikidata_id @en@skos:altLabel ?synonym
}
GROUP BY ?wikidata_id
ORDER BY ASC(?wikidata_id)
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
