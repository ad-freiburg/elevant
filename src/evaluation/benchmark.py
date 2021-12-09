from enum import Enum


class Benchmark(Enum):
    WIKI_EX = "wiki-ex"
    CONLL = "conll"
    CONLL_DEV = "conll-dev"
    CONLL_TEST = "conll-test"
    CONLL_PSEUDO_LINKS = "conll-links"
    ACE = "ace"
    MSNBC = "msnbc"
    ACE_ORIGINAL = "ace-original"
    MSNBC_ORIGINAL = "msnbc-original"
    WIKIPEDIA = "wikipedia"
    NEWSCRAWL = "newscrawl"
