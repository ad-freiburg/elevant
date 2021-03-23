from enum import Enum


class Linkers(Enum):
    BASELINE = "baseline"
    SPACY = "spacy"
    EXPLOSION = "explosion"
    AMBIVERSE = "ambiverse"
    IOB = "iob"
    TAGME = "tagme"
    WEXEA = "wexea"
    NEURAL_EL = "neural_el"
    TRAINED_MODEL = "trained_model"
    NONE = "none"


class LinkLinkers(Enum):
    LINK_LINKER = "link-linker"
    LINK_TEXT_LINKER = "link-text-linker"


class CoreferenceLinkers(Enum):
    NEURALCOREF = "neuralcoref"
    ENTITY = "entity"
    STANFORD = "stanford"
    XRENNER = "xrenner"
    HOBBS = "hobbs"
    WEXEA = "wexea"