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
    KB_COREF = "kb-coref"
    STANFORD = "stanford"
    # XRENNER = "xrenner"  # Xrenner has a dependency conflict with REL (flair)


class APILinkers(Enum):
    NIF_API = "nif-api"


class PredictionFormats(Enum):
    NIF = "nif"
    SIMPLE_JSONL = "simple-jsonl"
    AMBIVERSE = "ambiverse"
    WIKIFIER = "wikifier"
    EPGEL = "epgel"
    WEXEA = "wexea"
