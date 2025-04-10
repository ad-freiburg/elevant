import logging
import os
import json

logger = logging.getLogger("main." + __name__.split(".")[-1])

# Read data directory from config file
config_path = "configs/elevant.config.json"
config_data_directory = None
if os.path.exists(config_path):
    logger.info(f"Loading ELEVANT config from {config_path}")
    with open(config_path, "r", encoding="utf8") as file:
        config = json.load(file)
        config_data_directory = config.get("data_directory", None)

# In the docker container, the data directory is mounted to /data/
_DATA_DIRECTORIES = [
    config_data_directory,
    "/data/"
]
DATA_DIRECTORY = None
for directory in _DATA_DIRECTORIES:
    if os.path.exists(directory):
        DATA_DIRECTORY = directory.rstrip("/") + "/"
        break
if DATA_DIRECTORY is None:
    logger.error("Could not find the data directory.")
    exit(1)

# Wikipedia dump files
WIKIPEDIA_ARTICLES_PATH = DATA_DIRECTORY + "wikipedia-articles/"
WIKIDATA_MAPPINGS_PATH = DATA_DIRECTORY + "wikidata-mappings/"
WIKIPEDIA_MAPPINGS_PATH = DATA_DIRECTORY + "wikipedia-mappings/"
ARTICLE_SPLITS_PATH = DATA_DIRECTORY + "article-splits/"
EXTRACTED_WIKIPEDIA_ARTICLES = WIKIPEDIA_ARTICLES_PATH + "wikipedia.articles.jsonl"

# Article files
WIKIPEDIA_TRAINING_ARTICLES = ARTICLE_SPLITS_PATH + "wikipedia/training.jsonl"
WIKIPEDIA_DEVELOPMENT_ARTICLES = ARTICLE_SPLITS_PATH + "wikipedia/development.jsonl"
WIKIPEDIA_TEST_ARTICLES = ARTICLE_SPLITS_PATH + "wikipedia/test.jsonl"
DEV_AND_TEST_ARTICLE_IDS = "small-data-files/dev_and_test_article_ids.pkl"

NEWSCRAWL_DEVELOPMENT_ARTICLES = ARTICLE_SPLITS_PATH + "newscrawl/development.jsonl"
NEWSCRAWL_TEST_ARTICLES = ARTICLE_SPLITS_PATH + "newscrawl/test.jsonl"

# Wikidata mappings
QID_TO_ABSTRACTS_FILE = WIKIPEDIA_MAPPINGS_PATH + "qid_to_wikipedia_abstract.tsv"
QID_TO_GENDER_FILE = WIKIDATA_MAPPINGS_PATH + "qid_to_gender.tsv"
QID_TO_HUMAN_NAME_FILE = WIKIDATA_MAPPINGS_PATH + "qid_to_name.tsv"
QID_TO_DEMONYM_FILE = WIKIDATA_MAPPINGS_PATH + "qid_to_demonym.tsv"
QID_TO_LANGUAGE_FILE = WIKIDATA_MAPPINGS_PATH + "qid_to_language.tsv"
QID_TO_INSTANCE_OF_FILE = WIKIDATA_MAPPINGS_PATH + "qid_to_p31.tsv"
QID_TO_SUBCLASS_OF_FILE = WIKIDATA_MAPPINGS_PATH + "qid_to_p279.tsv"
QUANTITY_FILE = WIKIDATA_MAPPINGS_PATH + "quantity.tsv"
DATETIME_FILE = WIKIDATA_MAPPINGS_PATH + "datetime.tsv"
# Files to generate a mapping from QID to all its relevant types needed for our coref resolver
COARSE_TYPES = "small-data-files/coarse_types.tsv"
QID_TO_ALL_TYPES_FILE = WIKIDATA_MAPPINGS_PATH + "qid_to_all_types.tsv"
QID_TO_COREF_TYPES_FILE = WIKIDATA_MAPPINGS_PATH + "qid_to_coreference_types.tsv"
# Wikidata types files
WHITELIST_FILE = "small-data-files/whitelist_types.tsv"
WHITELIST_TYPE_ADJUSTMENTS_FILE = "small-data-files/type_adjustments.txt"

# Wikipedia mappings
LINK_FREEQUENCIES_FILE = WIKIPEDIA_MAPPINGS_PATH + "hyperlink_frequencies.pkl"
REDIRECTS_FILE = WIKIPEDIA_MAPPINGS_PATH + "redirects.pkl"
TITLE_SYNONYMS_FILE = WIKIPEDIA_MAPPINGS_PATH + "title_synonyms.pkl"
AKRONYMS_FILE = WIKIPEDIA_MAPPINGS_PATH + "akronyms.pkl"
WIKIPEDIA_ID_TO_TITLE_FILE = WIKIPEDIA_MAPPINGS_PATH + "wikipedia_id_to_title.tsv"
UNIGRAMS_FILE = WIKIPEDIA_MAPPINGS_PATH + "unigrams.txt"

# Database files
QID_TO_SITELINKS_DB = WIKIDATA_MAPPINGS_PATH + "qid_to_sitelinks.db"
QID_TO_LABEL_DB = WIKIDATA_MAPPINGS_PATH + "qid_to_label.db"
LABEL_TO_QIDS_DB = WIKIDATA_MAPPINGS_PATH + "label_to_qids.db"
QID_TO_WHITELIST_TYPES_DB = WIKIDATA_MAPPINGS_PATH + "qid_to_whitelist_types.db"
QID_TO_ALIASES_DB = WIKIDATA_MAPPINGS_PATH + "qid_to_aliases.db"
ALIAS_TO_QIDS_DB = WIKIDATA_MAPPINGS_PATH + "alias_to_qids.db"
WIKIPEDIA_NAME_TO_QID_DB = WIKIDATA_MAPPINGS_PATH + "wikipedia_name_to_qid.db"
REDIRECTS_DB = WIKIPEDIA_MAPPINGS_PATH + "redirects.db"
HYPERLINK_TO_MOST_POPULAR_CANDIDATES_DB = WIKIPEDIA_MAPPINGS_PATH + "hyperlink_to_most_popular_candidates.db"

# Custom mappings (have to be created by the user, e.g. using the scripts/extract_custom_mappings.py script)
CUSTOM_ENTITY_TO_NAME_FILE = DATA_DIRECTORY + "custom-mappings/entity_to_name.tsv"
CUSTOM_ENTITY_TO_TYPES_FILE = DATA_DIRECTORY + "custom-mappings/entity_to_types.tsv"
CUSTOM_WHITELIST_TYPES_FILE = DATA_DIRECTORY + "custom-mappings/whitelist_types.tsv"

# Linker files
LINKER_FILES = DATA_DIRECTORY + "linker-files/"
SPACY_MODEL_DIRECTORY = LINKER_FILES + "spacy/models/"

# Spacy knowledge base files
KB_FILE = LINKER_FILES + "spacy/knowledge_bases/wikidata/kb"
KB_DIRECTORY = LINKER_FILES + "spacy/knowledge_bases/"
VOCAB_DIRECTORY = LINKER_FILES + "spacy/knowledge_bases/wikidata/vocab"
VECTORS_DIRECTORY = LINKER_FILES + "spacy/knowledge_bases/vectors/"
VECTORS_ABSTRACTS_DIRECTORY = LINKER_FILES + "spacy/knowledge_bases/vectors/vectors_abstracts/"

# Benchmark files
BENCHMARK_DIR = "benchmarks/"

# Other files and paths
EVALUATION_RESULTS_DIR = "evaluation-results/"
LOG_PATH = "logs/"
TMP_FORKSERVER_CONFIG_FILE = "configs/tmp_forkserver.config.json"

# Other settings
LARGE_MODEL_NAME = "en_core_web_lg"

NER_IGNORE_TAGS = {
    "CARDINAL", "MONEY", "ORDINAL", "QUANTITY", "TIME"
}

TYPE_PERSON_QID = "Q215627"
TYPE_FICTIONAL_CHARACTER_QID = "Q95074"
TYPE_ORGANIZATION_QID = "Q43229"
TYPE_LOCATION_QID = "Q27096213"
TYPE_ETHNICITY_QID = "Q33829"
TYPE_LANGUOID_QID = "Q17376908"
