from enum import Enum


class Benchmark(Enum):
    OURS = "ours"
    CONLL = "conll"
    CONLL_PSEUDO_LINKS = "conll-links"
    ACE = "ace"
    MSNBC = "msnbc"
    WIKIPEDIA = "wikipedia"
