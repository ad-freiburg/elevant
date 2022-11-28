from enum import Enum


class Linkers(Enum):
    REFINED = "refined"
    TAGME = "tagme"
    DBPEDIA_SPOTLIGHT = "dbpedia-spotlight"
    REL = "rel"
    BASELINE = "baseline"
    SPACY = "spacy"
    POPULAR_ENTITIES = "popular-entities"
    POS_PRIOR = "pos-prior"
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
    EPGEL = "epgel"
