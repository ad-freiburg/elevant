import logging
import random
from typing import Optional, List

from elevant import settings
from elevant.benchmark_readers.aida_conll_benchmark_reader import AidaConllBenchmarkReader
from elevant.benchmark_readers.nif_benchmark_reader import NifBenchmarkReader
from elevant.benchmark_readers.oke_benchmark_reader import OkeBenchmarkReader
from elevant.benchmark_readers.our_jsonl_benchmark_reader import OurJsonlBenchmarkReader
from elevant.benchmark_readers.simple_jsonl_benchmark_reader import SimpleJsonlBenchmarkReader
from elevant.benchmark_readers.tagme_benchmark_reader import TagmeBenchmarkReader
from elevant.benchmark_readers.tsv_benchmark_reader import TsvBenchmarkReader
from elevant.benchmark_readers.xml_benchmark_reader import XMLBenchmarkReader
from elevant.evaluation.benchmark import BenchmarkFormat, Benchmark
from elevant.models.entity_database import EntityDatabase

logger = logging.getLogger("main." + __name__.split(".")[-1])

random.seed(42)


def get_benchmark_iterator(benchmark_name: str,
                           from_json_file: Optional[bool] = True,
                           benchmark_files: Optional[List[str]] = None,
                           benchmark_format: Optional[BenchmarkFormat] = None,
                           custom_kb: Optional[bool] = False):
    if custom_kb and benchmark_format not in {BenchmarkFormat.NIF.value, BenchmarkFormat.SIMPLE_JSONL.value}:
        logger.warning(f"Using a custom knowledge base is not supported for benchmark format {benchmark_format}. "
                       f"Please choose a different format.")
    if benchmark_files:
        if benchmark_format == BenchmarkFormat.NIF.value:
            entity_db = EntityDatabase()
            if not custom_kb:
                logger.info("Load mappings for NIF benchmark reader...")
                entity_db.load_wikipedia_to_wikidata_db()
                entity_db.load_redirects()
                logger.info("-> Mappings loaded.")
            benchmark_iterator = NifBenchmarkReader(entity_db, benchmark_files[0], custom_kb)
        elif benchmark_format == BenchmarkFormat.AIDA_CONLL.value:
            entity_db = EntityDatabase()
            logger.info("Load mappings for AIDA CoNLL benchmark reader...")
            entity_db.load_wikipedia_to_wikidata_db()
            entity_db.load_redirects()
            logger.info("-> Mappings loaded.")
            benchmark_iterator = AidaConllBenchmarkReader(entity_db, benchmark_files[0], benchmark_name)
        elif benchmark_format == BenchmarkFormat.SIMPLE_JSONL.value:
            entity_db = EntityDatabase()
            if not custom_kb:
                logger.info("Load mappings for Simple JSONL benchmark reader...")
                entity_db.load_wikipedia_to_wikidata_db()
                entity_db.load_redirects()
                logger.info("-> Mappings loaded.")
            benchmark_iterator = SimpleJsonlBenchmarkReader(entity_db, benchmark_files[0], custom_kb)
        elif benchmark_format == BenchmarkFormat.TSV.value:
            entity_db = EntityDatabase()
            logger.info("Load mappings for TSV benchmark reader...")
            entity_db.load_wikipedia_to_wikidata_db()
            entity_db.load_redirects()
            logger.info("-> Mappings loaded.")
            benchmark_iterator = TsvBenchmarkReader(entity_db, benchmark_files[0])
        elif benchmark_format == BenchmarkFormat.XML.value:
            if len(benchmark_files) == 1:
                raise IndexError("The XML benchmark reader needs the XML file and the directory with raw texts "
                                 "as input, but only one file was provided.")
            entity_db = EntityDatabase()
            logger.info("Load mappings for XML benchmark reader...")
            entity_db.load_wikipedia_to_wikidata_db()
            entity_db.load_redirects()
            logger.info("-> Mappings loaded.")
            benchmark_iterator = XMLBenchmarkReader(entity_db, benchmark_files[0], benchmark_files[1])
        elif benchmark_format == BenchmarkFormat.TAGME.value:
            if len(benchmark_files) == 1:
                raise IndexError("The TagMe benchmark reader needs the annotation file and the text snippet file "
                                 "as input, but only one file was provided.")
            entity_db = EntityDatabase()
            logger.info("Load mappings for TagMe benchmark reader...")
            entity_db.load_wikipedia_to_wikidata_db()
            entity_db.load_redirects()
            entity_db.load_wikipedia_id2wikipedia_title()
            logger.info("-> Mappings loaded.")
            benchmark_iterator = TagmeBenchmarkReader(entity_db, benchmark_files[0], benchmark_files[1])
        elif benchmark_format == BenchmarkFormat.OKE.value:
            entity_db = EntityDatabase()
            logger.info("Load mappings for OKE benchmark reader...")
            entity_db.load_wikipedia_to_wikidata_db()
            entity_db.load_redirects()
            logger.info("-> Mappings loaded.")
            benchmark_iterator = OkeBenchmarkReader(entity_db, benchmark_files[0])
        else:
            # Per default, assume OUR_JSONL format
            benchmark_iterator = OurJsonlBenchmarkReader(benchmark_files[0])
    elif from_json_file or benchmark_name in [Benchmark.WIKI_FAIR.value, Benchmark.NEWS_FAIR.value]:
        benchmark_filename = settings.BENCHMARK_DIR + benchmark_name + ".benchmark.jsonl"
        benchmark_iterator = OurJsonlBenchmarkReader(benchmark_filename)
    else:
        raise ValueError("%s is not a known benchmark." % benchmark_name)
    return benchmark_iterator
