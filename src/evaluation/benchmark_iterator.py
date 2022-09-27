import logging
import random
from typing import Optional

from src import settings
from src.benchmark_readers.aida_conll_benchmark_reader import AidaConllBenchmarkReader
from src.benchmark_readers.nif_benchmark_reader import NifBenchmarkReader
from src.benchmark_readers.our_jsonl_benchmark_reader import OurJsonlBenchmarkReader
from src.benchmark_readers.simple_jsonl_benchmark_reader import SimpleJsonlBenchmarkReader
from src.benchmark_readers.wikipedia_reader import WikipediaReader
from src.benchmark_readers.xml_benchmark_reader import XMLBenchmarkReader
from src.evaluation.benchmark import BenchmarkFormat, Benchmark
from src.models.entity_database import EntityDatabase

logger = logging.getLogger("main." + __name__.split(".")[-1])

random.seed(42)


def get_benchmark_iterator(benchmark_name: str, from_json_file: Optional[bool] = True,
                           benchmark_file: Optional[str] = None, benchmark_format: Optional[BenchmarkFormat] = None):
    if benchmark_file:
        if benchmark_format == BenchmarkFormat.NIF.value:
            logger.info("Load mappings for NIF benchmark reader...")
            entity_db = EntityDatabase()
            entity_db.load_wikipedia_wikidata_mapping()
            entity_db.load_redirects()
            logger.info("-> Mappings loaded.")
            benchmark_iterator = NifBenchmarkReader(entity_db, benchmark_file)
        elif benchmark_format == BenchmarkFormat.AIDA_CONLL.value:
            logger.info("Load mappings for AIDA CoNLL benchmark reader...")
            entity_db = EntityDatabase()
            entity_db.load_wikipedia_wikidata_mapping()
            entity_db.load_redirects()
            logger.info("-> Mappings loaded.")
            benchmark_iterator = AidaConllBenchmarkReader(entity_db, benchmark_file)
        elif benchmark_format == BenchmarkFormat.SIMPLE_JSONL.value:
            logger.info("Load mappings for Simple JSONL benchmark reader...")
            entity_db = EntityDatabase()
            entity_db.load_wikipedia_wikidata_mapping()
            entity_db.load_redirects()
            logger.info("-> Mappings loaded.")
            benchmark_iterator = SimpleJsonlBenchmarkReader(entity_db, benchmark_file)
        else:
            # Per default, assume OUR_JSONL format
            benchmark_iterator = OurJsonlBenchmarkReader(benchmark_file)
    elif from_json_file or benchmark_name in [Benchmark.WIKI_EX.value, Benchmark.NEWSCRAWL.value]:
        benchmark_filename = settings.BENCHMARK_DIR + benchmark_name + ".benchmark.jsonl"
        benchmark_iterator = OurJsonlBenchmarkReader(benchmark_filename)
    else:
        logger.info("Load mappings for benchmark reader...")
        entity_db = EntityDatabase()
        entity_db.load_wikipedia_wikidata_mapping()
        entity_db.load_redirects()
        logger.info("-> Mappings loaded.")
        if benchmark_name == Benchmark.ACE.value:
            benchmark_iterator = XMLBenchmarkReader(entity_db,
                                                    settings.ACE04_BENCHMARK_LABELS,
                                                    settings.ACE04_BENCHMARK_TEXTS)
        elif benchmark_name == Benchmark.MSNBC_UPDATED.value:
            benchmark_iterator = XMLBenchmarkReader(entity_db,
                                                    settings.MSNBC_BENCHMARK_LABELS,
                                                    settings.MSNBC_BENCHMARK_TEXTS)
        elif benchmark_name == Benchmark.ACE_ORIGINAL.value:
            benchmark_iterator = XMLBenchmarkReader(entity_db,
                                                    settings.ACE04_ORIGINAL_BENCHMARK_LABELS,
                                                    settings.ACE04_ORIGINAL_BENCHMARK_TEXTS)
        elif benchmark_name == Benchmark.MSNBC_ORIGINAL.value:
            benchmark_iterator = XMLBenchmarkReader(entity_db,
                                                    settings.MSNBC_ORIGINAL_BENCHMARK_LABELS,
                                                    settings.MSNBC_ORIGINAL_BENCHMARK_TEXTS)
        elif benchmark_name == Benchmark.WIKIPEDIA.value:
            benchmark_iterator = WikipediaReader(entity_db)
        elif benchmark_name in [Benchmark.AIDA_CONLL.value, Benchmark.AIDA_CONLL_TRAIN.value,
                                Benchmark.AIDA_CONLL_DEV.value, Benchmark.AIDA_CONLL_TEST.value]:
            benchmark_iterator = AidaConllBenchmarkReader(entity_db, settings.AIDA_CONLL_BENCHMARK_FILE,
                                                          benchmark_name)
        else:
            raise ValueError("%s is not a known benchmark." % benchmark_name)
    return benchmark_iterator
