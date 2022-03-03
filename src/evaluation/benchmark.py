from enum import Enum


class Benchmark(Enum):
    WIKI_EX = "wiki-ex"
    CONLL = "conll"
    CONLL_DEV = "conll-dev"
    CONLL_TEST = "conll-test"
    ACE = "ace"
    MSNBC = "msnbc"
    ACE_ORIGINAL = "ace-original"
    MSNBC_ORIGINAL = "msnbc-original"
    WIKIPEDIA = "wikipedia"
    NEWSCRAWL = "newscrawl"


class BenchmarkFormat(Enum):
    OURS_JSONL = "ours"
    NIF = "nif"
    # AIDA_JSON = "aida"  # Not yet supported: The format assumed by ConllExampleReader is not the typical AIDA format
    # MSNBC_XML = "msnbc"  # Not yet supported: 2 files are needed: annotation xml file/directory and raw text directory
