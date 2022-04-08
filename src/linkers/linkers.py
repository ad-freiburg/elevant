from enum import Enum


class Linkers(Enum):
    BASELINE = "baseline"
    SPACY = "spacy"
    EXPLOSION = "explosion"
    AMBIVERSE = "ambiverse"
    TAGME = "tagme"
    SIMPLE_JSONL = "simple_jsonl"
    BERT_MODEL = "bert_model"
    POPULAR_ENTITIES = "popular_entities"
    WIKIFIER = "wikifier"
    PURE_PRIOR = "pure_prior"
    POS_PRIOR = "pos_prior"
    NIF = "nif"
    NONE = "none"


class CoreferenceLinkers(Enum):
    NEURALCOREF = "neuralcoref"
    ENTITY = "entity"
    STANFORD = "stanford"
    XRENNER = "xrenner"
    HOBBS = "hobbs"
