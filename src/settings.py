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
DEV_AND_TEST_ARTICLE_IDS = "data/dev_and_test_article_ids.pkl"

NEWSCRAWL_DEVELOPMENT_ARTICLES = DATA_DIRECTORY + "articles/newscrawl/development.jsonl"
NEWSCRAWL_TEST_ARTICLES = DATA_DIRECTORY + "articles/newscrawl/test.jsonl"


# Wikidata mappings
WIKIDATA_ENTITIES_FILE = DATA_DIRECTORY + "wikidata_mappings/wikidata_entities.tsv"
QID_TO_ABSTRACTS_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_wikipedia_abstract.tsv"
QID_TO_WIKIPEDIA_URL_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_wikipedia_url.tsv"
QID_TO_GENDER_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_gender.tsv"
QID_TO_GIVEN_NAME_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_given_name.tsv"
QID_TO_SITELINK_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_sitelink.tsv"
QID_TO_DEMONYM_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_demonym.tsv"
QID_TO_LANGUAGE_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_language.tsv"
QID_TO_INSTANCE_OF_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_p31.tsv"
QID_TO_SUBCLASS_OF_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_p279.tsv"
QID_TO_LABEL_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_label.tsv"
QUANTITY_FILE = DATA_DIRECTORY + "wikidata_mappings/quantity.tsv"
DATETIME_FILE = DATA_DIRECTORY + "wikidata_mappings/datetime.tsv"
# Files to generate a mapping from QID to all its relevant types needed for our coref resolver
COARSE_TYPES = "data/coarse_types.tsv"
QID_TO_ALL_TYPES_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_all_types.tsv"
QID_TO_COREF_TYPES_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_coreference_types.tsv"
# Wikidata types files
WHITELIST_FILE = "data/whitelist_types.txt"
WHITELIST_TYPE_MAPPING = DATA_DIRECTORY + "wikidata_mappings/entity-types.tsv"


# Wikipedia mappings
LINK_FREEQUENCIES_FILE = DATA_DIRECTORY + "wikipedia_mappings/link_frequencies.pkl"
REDIRECTS_FILE = DATA_DIRECTORY + "wikipedia_mappings/link_redirects.pkl"
TITLE_SYNONYMS_FILE = DATA_DIRECTORY + "wikipedia_mappings/title_synonyms.pkl"
AKRONYMS_FILE = DATA_DIRECTORY + "wikipedia_mappings/akronyms.pkl"
WIKIPEDIA_ID_TO_TITLE_FILE = DATA_DIRECTORY + "wikipedia_mappings/wikipedia_id_to_title.tsv"
UNIGRAMS_FILE = DATA_DIRECTORY + "wikipedia_mappings/unigrams.txt"
WIKIPEDIA_ABSTRACTS_FILE = DATA_DIRECTORY + "wikipedia_mappings/article_abstracts.tsv"

# Spacy knowledge base files
KB_FILE = DATA_DIRECTORY + "spacy_knowledge_bases/wikidata/kb"
KB_DIRECTORY = DATA_DIRECTORY + "spacy_knowledge_bases/wikidata/"
VOCAB_DIRECTORY = DATA_DIRECTORY + "spacy_knowledge_bases/wikidata/vocab"
VECTORS_DIRECTORY = DATA_DIRECTORY + "spacy_knowledge_bases/vectors/vectors"
VECTORS_ABSTRACTS_DIRECTORY = DATA_DIRECTORY + "spacy_knowledge_bases/vectors/vectors_abstracts/"

# Linker files
LINKERS_DIRECTORY = DATA_DIRECTORY + "linker_files/trained_spacy_linker_models/"

LINKER_MODEL_PATH = DATA_DIRECTORY + "linker_files/nn_linker_models/"
RDF2VEC_MODEL_PATH = DATA_DIRECTORY + "linker_files/entity_embeddings/wikid2vec_sg_500_7_4_15_4_500"


# Benchmark files
CONLL_BENCHMARK_FILE = DATA_DIRECTORY + "benchmarks/conll/conll-wikidata-iob-annotations"

ACE04_BENCHMARK_TEXTS = DATA_DIRECTORY + "benchmarks/ace2004/RawText/"
ACE04_BENCHMARK_LABELS = DATA_DIRECTORY + "benchmarks/ace2004/ace2004.xml"

ACE04_ORIGINAL_BENCHMARK_TEXTS = DATA_DIRECTORY + "benchmarks/ace2004.original/RawTextsNoTranscripts/"
ACE04_ORIGINAL_BENCHMARK_LABELS = DATA_DIRECTORY + "benchmarks/ace2004.original/ProblemsNoTranscripts/"

MSNBC_BENCHMARK_TEXTS = DATA_DIRECTORY + "benchmarks/msnbc/RawText/"
MSNBC_BENCHMARK_LABELS = DATA_DIRECTORY + "benchmarks/msnbc/msnbc.xml"

MSNBC_ORIGINAL_BENCHMARK_TEXTS = DATA_DIRECTORY + "benchmarks/msnbc.original/RawTextsSimpleChars_utf8/"
MSNBC_ORIGINAL_BENCHMARK_LABELS = DATA_DIRECTORY + "benchmarks/msnbc.original/Problems/"

WIKI_EX_BENCHMARK_FILE = "benchmarks/benchmark_labels_wiki-ex.jsonl"


# Other files and paths
LOG_PATH = "logs/"


# Other settings
LARGE_MODEL_NAME = "en_core_web_lg"

NER_IGNORE_TAGS = {
    "CARDINAL", "MONEY", "ORDINAL", "QUANTITY", "TIME"
}
