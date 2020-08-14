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
ARTICLE_JSON_FILE = "/nfs/students/natalie-prange/wiki_files/wiki_dump_with_links.json"

SPLIT_ARTICLES_DIR = DATA_DIRECTORY + "articles_split/"
TRAINING_ARTICLES = SPLIT_ARTICLES_DIR + "training.txt"
DEVELOPMENT_ARTICLES = SPLIT_ARTICLES_DIR + "development.txt"
TEST_ARTICLES = SPLIT_ARTICLES_DIR + "test.txt"

DATABASE_DIRECTORY = DATA_DIRECTORY + "yi-chun/"
ENTITY_FILE = DATABASE_DIRECTORY + "wikidata-entities-large.tsv"
PERSON_NAMES_FILE = DATABASE_DIRECTORY + "wikidata-familyname.csv"
ABSTRACTS_FILE = DATABASE_DIRECTORY + "wikidata-wikipedia.tsv"
WIKI_MAPPING_FILE = DATABASE_DIRECTORY + "wikidata-wikipedia-mapping.csv"
GENDER_MAPPING_FILE = "/nfs/students/natalie-prange/wikidata_mappings/qid_to_gender.tsv"

LINK_FREEQUENCIES_FILE = DATA_DIRECTORY + "link_frequencies.pkl"
REDIRECTS_FILE = DATA_DIRECTORY + "link_redirects.pkl"

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

OWN_BENCHMARK_DIRECOTRY = DATA_DIRECTORY + "benchmark/"
OWN_BENCHMARK_FILE = OWN_BENCHMARK_DIRECOTRY + "development_labels.jsonl"
