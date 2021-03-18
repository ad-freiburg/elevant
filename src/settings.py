import os


_DATA_DIRECTORIES = [
    "/home/hertel/wikipedia/wikipedia_2020-06-08/",
    "/local/data/hertelm/wikipedia_2020-06-08/",
    "/nfs/students/matthias-hertel/wiki_entity_linker/",
    "/data/"
]
DATA_DIRECTORY = None
for directory in _DATA_DIRECTORIES:
    if os.path.exists(directory):
        DATA_DIRECTORY = directory
        break
if DATA_DIRECTORY is None:
    print("ERROR: could not find the data directory.")
    exit(1)

ARTICLE_JSON_DIR = DATA_DIRECTORY + "json/"
ARTICLE_JSON_FILE = DATA_DIRECTORY + "wiki_extractor_output/wiki_dump_with_links_and_bold.jsonl"

SPLIT_ARTICLES_DIR = DATA_DIRECTORY + "articles_split/"
TRAINING_ARTICLES = SPLIT_ARTICLES_DIR + "training_bold.jsonl"
DEVELOPMENT_ARTICLES = SPLIT_ARTICLES_DIR + "development_bold.jsonl"
TEST_ARTICLES = SPLIT_ARTICLES_DIR + "test_bold.jsonl"

DATABASE_DIRECTORY = DATA_DIRECTORY + "yi-chun/"
ENTITY_FILE = DATABASE_DIRECTORY + "wikidata-entities-large.tsv"
PERSON_NAMES_FILE = DATABASE_DIRECTORY + "wikidata-familyname.csv"
ABSTRACTS_FILE = DATABASE_DIRECTORY + "wikidata-wikipedia.tsv"
WIKI_MAPPING_FILE = DATABASE_DIRECTORY + "wikidata-wikipedia-mapping.csv"

GENDER_MAPPING_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_gender.tsv"
GIVEN_NAME_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_given_name.tsv"
TYPE_MAPPING_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_categories_v9.txt"
ALL_TYPES_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_all_classes.txt"
RELEVANT_TYPES_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_relevant_classes.txt"
WIKIDATA_SITELINK_COUNTS_FILE = DATA_DIRECTORY + "wikidata_sitelink_counts.txt"
DEMONYM_FILE = DATA_DIRECTORY + "qid_to_demonym.tsv"

LINK_FREEQUENCIES_FILE = DATA_DIRECTORY + "link_frequencies.pkl"
REDIRECTS_FILE = DATA_DIRECTORY + "link_redirects.pkl"
TITLE_SYNONYMS_FILE = DATA_DIRECTORY + "title_synonyms.pkl"
AKRONYMS_FILE = DATA_DIRECTORY + "akronyms.pkl"

ENTITY_PREFIX = "http://www.wikidata.org/entity/"

LARGE_MODEL_NAME = "en_core_web_lg"

KB_FILE = DATA_DIRECTORY + "kb"
KB_DIRECTORY = DATA_DIRECTORY + "knowledge_bases/"
VOCAB_DIRECTORY = DATA_DIRECTORY + "vocab"

VECTORS_DIRECTORY = DATA_DIRECTORY + "vectors/"
VECTORS_FILE = DATA_DIRECTORY + "vectors.pkl"

LINKERS_DIRECTORY = DATA_DIRECTORY + "linkers/"

NER_IGNORE_TAGS = {
    "CARDINAL", "MONEY", "ORDINAL", "QUANTITY", "TIME"
}

CONLL_BENCHMARK_DIRECTORY = DATA_DIRECTORY + "conll/"
CONLL_BENCHMARK_FILE = CONLL_BENCHMARK_DIRECTORY + "conll-wikidata-iob-annotations"

ACE04_ORIGINAL_BENCHMARK_TEXTS = DATA_DIRECTORY + "ace2004.original/RawTextsNoTranscripts"
ACE04_ORIGINAL_BENCHMARK_LABELS = DATA_DIRECTORY + "ace2004.original/ProblemsNoTranscripts/"

ACE04_BENCHMARK_TEXTS = DATA_DIRECTORY + "ace2004.updated/RawText/"
ACE04_BENCHMARK_LABELS = DATA_DIRECTORY + "ace2004.updated/ace2004.xml"

MSNBC_ORIGINAL_BENCHMARK_TEXTS = DATA_DIRECTORY + "msnbc.original/RawTextsSimpleChars_utf8/"
MSNBC_ORIGINAL_BENCHMARK_LABELS = DATA_DIRECTORY + "msnbc.original/Problems/"

MSNBC_BENCHMARK_TEXTS = DATA_DIRECTORY + "msnbc.updated/RawText/"
MSNBC_BENCHMARK_LABELS = DATA_DIRECTORY + "msnbc.updated/msnbc.xml"

OWN_BENCHMARK_DIRECOTRY = DATA_DIRECTORY + "benchmark/"
OWN_BENCHMARK_FILE = OWN_BENCHMARK_DIRECOTRY + "development_labels_bold.jsonl"

UNIGRAMS_FILE = DATA_DIRECTORY + "unigrams.txt"

LINKER_MODEL_PATH = "/nfs/students/natalie-prange/wiki-entity-linker_data/linker_models/"
RDF2VEC_MODEL_PATH = "/nfs/students/natalie-prange/wiki-entity-linker_data/entity_embeddings/wikid2vec_sg_500_7_4_15_4_500"
