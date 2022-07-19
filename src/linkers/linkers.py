from enum import Enum


class Linkers(Enum):
    BASELINE = "baseline"
    SPACY = "spacy"
    EXPLOSION = "explosion"
    TAGME = "tagme"
    BERT_MODEL = "bert_model"
    POPULAR_ENTITIES = "popular_entities"
    POS_PRIOR = "pos_prior"
    DBPEDIA_SPOTLIGHT = "dbpedia_spotlight"
    NONE = "none"


class CoreferenceLinkers(Enum):
    NEURALCOREF = "neuralcoref"
    ENTITY = "entity"
    STANFORD = "stanford"
    XRENNER = "xrenner"


class PredictionFormats(Enum):
    NIF = "nif"
    SIMPLE_JSONL = "simple_jsonl"
    AMBIVERSE = "ambiverse"
    WIKIFIER = "wikifier"
