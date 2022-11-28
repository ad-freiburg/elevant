from enum import Enum


class Linkers(Enum):
    BASELINE = "baseline"
    SPACY = "spacy"
    TAGME = "tagme"
    POPULAR_ENTITIES = "popular-entities"
    POS_PRIOR = "pos-prior"
    DBPEDIA_SPOTLIGHT = "dbpedia-spotlight"
    REFINED = "refined"
    REL = "rel"
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
