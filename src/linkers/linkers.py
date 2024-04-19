from enum import Enum


class Linkers(Enum):
    REFINED = "refined"
    REL = "rel"
    GPT = "gpt"
    TAGME = "tagme"
    WAT = "wat"
    DBPEDIA_SPOTLIGHT = "dbpedia-spotlight"
    BABELFY = "babelfy"
    BASELINE = "baseline"
    SPACY = "spacy"
    POPULAR_ENTITIES = "popular-entities"
    POS_PRIOR = "pos-prior"
    NONE = "none"


class CoreferenceLinkers(Enum):
    # NEURALCOREF = "neuralcoref"  # Neuralcoref is outdated, see ELEVANT Github issue #5
    FASTCOREF = "fastcoref"
    ENTITY = "entity"
    STANFORD = "stanford"
    # XRENNER = "xrenner"  # Xrenner has a dependency conflict with REL (flair)


class PredictionFormats(Enum):
    NIF = "nif"
    SIMPLE_JSONL = "simple-jsonl"
    AMBIVERSE = "ambiverse"
    WIKIFIER = "wikifier"
    EPGEL = "epgel"
