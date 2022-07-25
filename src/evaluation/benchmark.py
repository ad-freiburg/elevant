from enum import Enum
import os
import re

from src import settings


def get_available_benchmarks():
    benchmark_names = []
    for filename in sorted(os.listdir(settings.BENCHMARK_DIR)):
        match = re.match(r"(.*)\.benchmark\.jsonl", filename)
        if match:
            benchmark_names.append(match.group(1))
    return benchmark_names


class Benchmark(Enum):
    WIKI_EX = "wiki-ex"
    AIDA_CONLL = "aida-conll"
    AIDA_CONLL_TRAIN = "aida-conll-train"
    AIDA_CONLL_DEV = "aida-conll-dev"
    AIDA_CONLL_TEST = "aida-conll-test"
    ACE = "ace"
    ACE_ORIGINAL = "ace-original"
    MSNBC_UPDATED = "msnbc-updated"
    MSNBC_ORIGINAL = "msnbc"
    WIKIPEDIA = "wikipedia"
    NEWSCRAWL = "newscrawl"


class BenchmarkFormat(Enum):
    OURS_JSONL = "ours"
    NIF = "nif"
    AIDA_CONLL = "aida-conll"
    SIMPLE_JSONL = "simple-jsonl"
    # MSNBC_XML = "msnbc"  # Not yet supported: 2 files are needed: annotation xml file/directory and raw text directory
