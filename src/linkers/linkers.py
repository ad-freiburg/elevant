from enum import Enum


class Linkers(Enum):
    BASELINE = "baseline"
    SPACY = "spacy"
    TAGME = "tagme"
    BERT_MODEL = "bert-model"
    POPULAR_ENTITIES = "popular-entities"
    POS_PRIOR = "pos-prior"
    DBPEDIA_SPOTLIGHT = "dbpedia-spotlight"
    NONE = "none"


class CoreferenceLinkers(Enum):
    NEURALCOREF = "neuralcoref"
    ENTITY = "entity"
    STANFORD = "stanford"
    XRENNER = "xrenner"


class PredictionFormats(Enum):
    NIF = "nif"
    SIMPLE_JSONL = "simple-jsonl"
    AMBIVERSE = "ambiverse"
    WIKIFIER = "wikifier"
