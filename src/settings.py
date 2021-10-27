import os


_DATA_DIRECTORIES = [
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

# Base files
ARTICLE_JSON_FILE = DATA_DIRECTORY + "wikipedia_dump_files/wiki_dump_with_links_and_bold.jsonl"


# Article files
WIKIPEDIA_TRAINING_ARTICLES = DATA_DIRECTORY + "articles/wikipedia/training_bold.jsonl"
WIKIPEDIA_DEVELOPMENT_ARTICLES = DATA_DIRECTORY + "articles/wikipedia/development_bold.jsonl"
WIKIPEDIA_TEST_ARTICLES = DATA_DIRECTORY + "articles/wikipedia/test_bold.jsonl"

NEWSCRAWL_DEVELOPMENT_ARTICLES = DATA_DIRECTORY + "articles/newscrawl/development.jsonl"
NEWSCRAWL_TEST_ARTICLES = DATA_DIRECTORY + "articles/newscrawl/test.jsonl"


# Wikidata mappings
ENTITY_FILE = DATA_DIRECTORY + "wikidata_mappings/wikidata_entities.tsv"
ABSTRACTS_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_wikipedia_abstract.tsv"
WIKI_MAPPING_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_wikipedia_url.tsv"

GENDER_MAPPING_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_gender.tsv"
GIVEN_NAME_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_given_name.tsv"
TYPE_MAPPING_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_categories_v9.txt"
ALL_TYPES_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_all_classes.txt"
RELEVANT_TYPES_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_relevant_classes.txt"
WIKIDATA_SITELINK_COUNTS_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_sitelinks.txt"
DEMONYM_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_demonym.tsv"
LANGUAGE_FILE = DATA_DIRECTORY + "wikidata_mappings/qid_to_language.tsv"
REAL_NUMBERS = DATA_DIRECTORY + "wikidata_mappings/real_numbers.tsv"
POINTS_IN_TIME = DATA_DIRECTORY + "wikidata_mappings/point_in_time.tsv"

WHITELIST_TYPE_MAPPING = DATA_DIRECTORY + "wikidata_mappings/entity-types.ttl"
LABEL_MAPPING = DATA_DIRECTORY + "wikidata_mappings/qid_to_label.tsv"
WHITELIST_FILE = "wikidata-types/types.txt"


# Wikipedia mappings
LINK_FREEQUENCIES_FILE = DATA_DIRECTORY + "wikipedia_mappings/link_frequencies.pkl"
REDIRECTS_FILE = DATA_DIRECTORY + "wikipedia_mappings/link_redirects.pkl"
TITLE_SYNONYMS_FILE = DATA_DIRECTORY + "wikipedia_mappings/title_synonyms.pkl"
AKRONYMS_FILE = DATA_DIRECTORY + "wikipedia_mappings/akronyms.pkl"
WIKIPEDIA_ID_TO_TITLE_FILE = DATA_DIRECTORY + "wikipedia_mappings/wikipedia_id_to_title.tsv"
UNIGRAMS_FILE = DATA_DIRECTORY + "wikipedia_mappings/unigrams.txt"


# Spacy knowledge base files
KB_FILE = DATA_DIRECTORY + "spacy_knowledge_bases/wikidata/kb"
KB_DIRECTORY = DATA_DIRECTORY + "spacy_knowledge_bases/"
VOCAB_DIRECTORY = DATA_DIRECTORY + "spacy_knowledge_bases/vocab"
VECTORS_DIRECTORY = DATA_DIRECTORY + "spacy_knowledge_bases/vectors/vectors"
VECTORS_ABSTRACTS_DIRECTORY = DATA_DIRECTORY + "spacy_knowledge_bases/vectors/vectors_abstracts/"

# Linker files
LINKERS_DIRECTORY = DATA_DIRECTORY + "linker_files/linker_files/trained_spacy_linker_models/"

LINKER_MODEL_PATH = DATA_DIRECTORY + "linker_files/nn_linker_models/"
RDF2VEC_MODEL_PATH = "/linker_files/entity_embeddings/wikid2vec_sg_500_7_4_15_4_500"


# Benchmark files
CONLL_BENCHMARK_FILE = DATA_DIRECTORY + "benchmarks/conll/conll-wikidata-iob-annotations"

ACE04_BENCHMARK_TEXTS = DATA_DIRECTORY + "benchmarks/ace2004/RawText/"
ACE04_BENCHMARK_LABELS = DATA_DIRECTORY + "benchmarks/ace2004/ace2004.xml"

MSNBC_BENCHMARK_TEXTS = DATA_DIRECTORY + "benchmarks/msnbc/RawText/"
MSNBC_BENCHMARK_LABELS = DATA_DIRECTORY + "benchmarks/msnbc/msnbc.xml"

OWN_BENCHMARK_FILE = "benchmarks/benchmark_labels_ours.jsonl"


# Other settings
ENTITY_PREFIX = "http://www.wikidata.org/entity/"

LARGE_MODEL_NAME = "en_core_web_lg"

NER_IGNORE_TAGS = {
    "CARDINAL", "MONEY", "ORDINAL", "QUANTITY", "TIME"
}
