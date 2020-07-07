import os


_DATA_DIRECTORIES = [
    "/home/hertel/wikipedia/wikipedia_2020-06-08/",
    "/local/data/hertelm/wikipedia_2020-06-08/"
]
DATA_DIRECTORY = None
for directory in _DATA_DIRECTORIES:
    if os.path.exists(directory):
        DATA_DIRECTORY = directory
        break
if DATA_DIRECTORY is None:
    print("ERROR: could not find the data directory.")
    exit(1)

DATABASE_DIRECTORY = DATA_DIRECTORY + "yi-chun/"
ENTITY_FILE = DATABASE_DIRECTORY + "wikidata-entities-large.tsv"
PERSON_NAMES_FILE = DATABASE_DIRECTORY + "wikidata-familyname.csv"
ABSTRACTS_FILE = DATABASE_DIRECTORY + "wikidata-wikipedia.tsv"
LINKS_FILE = DATABASE_DIRECTORY + "wikidata-wikipedia-mapping.csv"

TRAINING_PARAGRAPHS_FILE = DATA_DIRECTORY + "training.txt"
DEVELOPMENT_PARAGRAPHS_FILE = DATA_DIRECTORY + "development.txt"

LINK_COUNTS_FILE = DATA_DIRECTORY + "link_counts.pkl"

ENTITY_PREFIX = "http://www.wikidata.org/entity/"

LARGE_MODEL_NAME = "en_core_web_lg"

KB_FILE = DATA_DIRECTORY + "kb"
VOCAB_DIRECTORY = DATA_DIRECTORY + "vocab"

VECTORS_DIRECTORY = DATA_DIRECTORY + "vectors/"
VECTORS_FILE = DATA_DIRECTORY + "vectors.pkl"

LINKER_DIRECTORY = DATA_DIRECTORY + "linker"
