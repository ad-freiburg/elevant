import logging
import os

logger = logging.getLogger("main." + __name__.split(".")[-1])


_DATA_DIRECTORIES = [
    "/local/data/entity-linking/",
    "/data/"
]
DATA_DIRECTORY = None
for directory in _DATA_DIRECTORIES:
    if os.path.exists(directory):
        DATA_DIRECTORY = directory
        break
if DATA_DIRECTORY is None:
    logger.error("Could not find the data directory.")
    exit(1)

# Base files
WIKIPEDIA_DUMP_PATH = DATA_DIRECTORY + "wikipedia_dump_files/"
EXTRACTED_WIKIPEDIA_DUMP_NAME = "enwiki-latest-extracted.jsonl"
EXTRACTED_WIKIPEDIA_DUMP_FILE = WIKIPEDIA_DUMP_PATH + EXTRACTED_WIKIPEDIA_DUMP_NAME


# Article files
WIKIPEDIA_TRAINING_ARTICLES = DATA_DIRECTORY + "articles/wikipedia/training.jsonl"
WIKIPEDIA_DEVELOPMENT_ARTICLES = DATA_DIRECTORY + "articles/wikipedia/development.jsonl"
WIKIPEDIA_TEST_ARTICLES = DATA_DIRECTORY + "articles/wikipedia/test.jsonl"
DEV_AND_TEST_ARTICLE_IDS = "small-data-files/dev_and_test_article_ids.pkl"

NEWSCRAWL_DEVELOPMENT_ARTICLES = DATA_DIRECTORY + "articles/newscrawl/development.jsonl"
NEWSCRAWL_TEST_ARTICLES = DATA_DIRECTORY + "articles/newscrawl/test.jsonl"


# Wikidata mappings
QID_TO_ABSTRACTS_FILE = DATA_DIRECTORY + "wikipedia_mappings/qid_to_wikipedia_abstract.tsv"
QID_TO_GENDER_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_gender.tsv"
QID_TO_HUMAN_NAME_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_name.tsv"
QID_TO_DEMONYM_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_demonym.tsv"
QID_TO_LANGUAGE_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_language.tsv"
QID_TO_INSTANCE_OF_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_p31.tsv"
QID_TO_SUBCLASS_OF_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_p279.tsv"
QUANTITY_FILE = DATA_DIRECTORY + "wikidata_mappings/quantity.tsv"
DATETIME_FILE = DATA_DIRECTORY + "wikidata_mappings/datetime.tsv"
# Files to generate a mapping from QID to all its relevant types needed for our coref resolver
COARSE_TYPES = "small-data-files/coarse_types.tsv"
QID_TO_ALL_TYPES_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_all_types.tsv"
QID_TO_COREF_TYPES_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_coreference_types.tsv"
# Wikidata types files
WHITELIST_FILE = "small-data-files/whitelist_types.tsv"
WHITELIST_TYPE_ADJUSTMENTS_FILE = "small-data-files/type_adjustments.txt"

# Wikipedia mappings
LINK_FREEQUENCIES_FILE = DATA_DIRECTORY + "wikipedia_mappings/hyperlink_frequencies.pkl"
REDIRECTS_FILE = DATA_DIRECTORY + "wikipedia_mappings/redirects.pkl"
TITLE_SYNONYMS_FILE = DATA_DIRECTORY + "wikipedia_mappings/title_synonyms.pkl"
AKRONYMS_FILE = DATA_DIRECTORY + "wikipedia_mappings/akronyms.pkl"
WIKIPEDIA_ID_TO_TITLE_FILE = DATA_DIRECTORY + "wikipedia_mappings/wikipedia_id_to_title.tsv"
UNIGRAMS_FILE = DATA_DIRECTORY + "wikipedia_mappings/unigrams.txt"

# Database files
QID_TO_SITELINKS_DB = DATA_DIRECTORY + "wikidata_mappings/qid_to_sitelinks.db"
QID_TO_LABEL_DB = DATA_DIRECTORY + "wikidata_mappings/qid_to_label.db"
LABEL_TO_QIDS_DB = DATA_DIRECTORY + "wikidata_mappings/label_to_qids.db"
QID_TO_WHITELIST_TYPES_DB = DATA_DIRECTORY + "wikidata_mappings/qid_to_whitelist_types.db"
QID_TO_ALIASES_DB = DATA_DIRECTORY + "wikidata_mappings/qid_to_aliases.db"
ALIAS_TO_QIDS_DB = DATA_DIRECTORY + "wikidata_mappings/alias_to_qids.db"
WIKIPEDIA_NAME_TO_QID_DB = DATA_DIRECTORY + "wikidata_mappings/wikipedia_name_to_qid.db"
REDIRECTS_DB = DATA_DIRECTORY + "wikipedia_mappings/redirects.db"
HYPERLINK_TO_MOST_POPULAR_CANDIDATES_DB = DATA_DIRECTORY + "wikipedia_mappings/hyperlink_to_most_popular_candidates.db"

# Custom mappings (have to be created by the user, e.g. using the scripts/extract_custom_mappings.py script)
CUSTOM_ENTITY_TO_NAME_FILE = DATA_DIRECTORY + "custom_mappings/entity_to_name.tsv"
CUSTOM_ENTITY_TO_TYPES_FILE = DATA_DIRECTORY + "custom_mappings/entity_to_types.tsv"
CUSTOM_WHITELIST_TYPES_FILE = DATA_DIRECTORY + "custom_mappings/whitelist_types.tsv"

# Spacy knowledge base files
KB_FILE = DATA_DIRECTORY + "linker_files/spacy/knowledge_bases/wikidata/kb"
KB_DIRECTORY = DATA_DIRECTORY + "linker_files/spacy/knowledge_bases/"
VOCAB_DIRECTORY = DATA_DIRECTORY + "linker_files/spacy/knowledge_bases/wikidata/vocab"
VECTORS_DIRECTORY = DATA_DIRECTORY + "linker_files/spacy/knowledge_bases/vectors/"
VECTORS_ABSTRACTS_DIRECTORY = DATA_DIRECTORY + "linker_files/spacy/knowledge_bases/vectors/vectors_abstracts/"

# Linker files
LINKER_FILES = DATA_DIRECTORY + "linker_files/"
SPACY_MODEL_DIRECTORY = LINKER_FILES + "spacy/models/"

# Benchmark files
AIDA_CONLL_BENCHMARK_FILE = DATA_DIRECTORY + "benchmarks/aida/AIDA-YAGO2-dataset.tsv"

BENCHMARK_DIR = "benchmarks/"
WIKI_EX_BENCHMARK_FILE = BENCHMARK_DIR + "wiki-ex.benchmark.jsonl"

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
