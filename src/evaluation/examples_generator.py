from typing import Iterator, Tuple, Optional

from src.benchmark_readers.simple_jsonl_benchmark_reader import SimpleJsonlBenchmarkReader
from src.evaluation.benchmark import Benchmark, BenchmarkFormat
from src.evaluation.groundtruth_label import GroundtruthLabel
from src.benchmark_readers.aida_conll_benchmark_reader import AidaConllBenchmarkReader
from src.benchmark_readers.nif_benchmark_reader import NifBenchmarkReader
from src.helpers.wikipedia_corpus import WikipediaCorpus
from src.models.article import Article
from src.models.entity_database import EntityDatabase
from src.models.article import article_from_json
from src.benchmark_readers.xml_benchmark_reader import XMLBenchmarkParser
from src import settings

import random
import logging

logger = logging.getLogger("main." + __name__.split(".")[-1])

random.seed(42)


def expand_span(text: str, span: Tuple[int, int]) -> Tuple[int, int]:
    begin, end = span
    while begin - 1 > 0 and text[begin - 1].isalpha():
        begin = begin - 1
    while end < len(text) and text[end].isalpha():
        end = end + 1
    return begin, end


class WikipediaExampleReader:
    def __init__(self, entity_db: EntityDatabase):
        self.entity_db = entity_db

    def iterate(self, n: int = -1) -> Iterator[Article]:
        for article in WikipediaCorpus.development_articles(n):
            article.labels = []
            label_id_counter = 0
            for span, target in article.hyperlinks:
                span = expand_span(article.text, span)
                entity_id = self.entity_db.link2id(target)
                if entity_id is None:
                    entity_id = "Unknown"
                gt_label = GroundtruthLabel(label_id_counter, span, entity_id, "Unknown")
                article.labels.append(gt_label)
                label_id_counter += 1
            yield article


class XMLExampleReader:
    def __init__(self, entity_db: EntityDatabase, labels_file_or_dir: str, text_dir: str):
        self.entity_db = entity_db
        self.labels_file_or_dir = labels_file_or_dir
        self.text_dir = text_dir

    def iterate(self, n: int = -1) -> Iterator[Article]:
        parser = XMLBenchmarkParser(self.entity_db)
        for i, article in enumerate(parser.article_iterator(self.labels_file_or_dir,
                                                            self.text_dir)):
            if i == n:
                break
            yield article


class NifExampleReader:
    def __init__(self, entity_db: EntityDatabase, benchmark_path: str):
        self.entity_db = entity_db
        self.benchmark_path = benchmark_path

    def iterate(self, n: int = -1) -> Iterator[Article]:
        parser = NifBenchmarkReader(self.entity_db)
        for i, article in enumerate(parser.article_iterator(self.benchmark_path)):
            if i == n:
                break
            yield article


class AidaConllExampleReader:
    def __init__(self, entity_db: EntityDatabase, benchmark_path: str, benchmark: Optional[str] = None):
        self.entity_db = entity_db
        self.benchmark_path = benchmark_path
        self.benchmark = benchmark

    def iterate(self, n: int = -1) -> Iterator[Article]:
        parser = AidaConllBenchmarkReader(self.entity_db)
        for i, article in enumerate(parser.article_iterator(self.benchmark_path, self.benchmark)):
            if i == n:
                break
            yield article


class SimpleJsonlExampleReader:
    def __init__(self, entity_db: EntityDatabase, benchmark_path: str):
        self.entity_db = entity_db
        self.benchmark_path = benchmark_path

    def iterate(self, n: int = -1) -> Iterator[Article]:
        parser = SimpleJsonlBenchmarkReader(self.entity_db)
        for i, article in enumerate(parser.article_iterator(self.benchmark_path)):
            if i == n:
                break
            yield article


class JsonBenchmarkExampleReader:
    def __init__(self, benchmark_filename: str):
        self.benchmark_filename = benchmark_filename

    def iterate(self, n: int = -1) -> Iterator[Article]:
        with open(self.benchmark_filename, "r") as benchmark_file:
            for i, json_line in enumerate(benchmark_file):
                if i == n:
                    break
                article = article_from_json(json_line)
                yield article


def get_example_generator(benchmark_name: str, from_json_file: Optional[bool] = True,
                          benchmark_file: Optional[str] = None, benchmark_format: Optional[BenchmarkFormat] = None):
    if benchmark_file:
        if benchmark_format == BenchmarkFormat.NIF.value:
            logger.info("Load mappings for NIF example generator...")
            entity_db = EntityDatabase()
            entity_db.load_wikipedia_wikidata_mapping()
            entity_db.load_redirects()
            logger.info("-> Mappings loaded.")
            example_generator = NifExampleReader(entity_db, benchmark_file)
        elif benchmark_format == BenchmarkFormat.AIDA_CONLL.value:
            logger.info("Load mappings for AIDA CoNLL example generator...")
            entity_db = EntityDatabase()
            entity_db.load_wikipedia_wikidata_mapping()
            entity_db.load_redirects()
            logger.info("-> Mappings loaded.")
            example_generator = AidaConllExampleReader(entity_db, benchmark_file)
        elif benchmark_format == BenchmarkFormat.SIMPLE_JSONL.value:
            logger.info("Load mappings for Simple JSONL example generator...")
            entity_db = EntityDatabase()
            entity_db.load_wikipedia_wikidata_mapping()
            entity_db.load_redirects()
            logger.info("-> Mappings loaded.")
            example_generator = SimpleJsonlExampleReader(entity_db, benchmark_file)
        else:
            # Per default, assume OUR_JSONL format
            example_generator = JsonBenchmarkExampleReader(benchmark_file)
    elif from_json_file:
        benchmark_filename = settings.BENCHMARK_DIR + benchmark_name + ".benchmark.jsonl"
        example_generator = JsonBenchmarkExampleReader(benchmark_filename)
    else:
        if benchmark_name == Benchmark.WIKI_EX.value:
            example_generator = JsonBenchmarkExampleReader(settings.WIKI_EX_BENCHMARK_FILE)
        elif benchmark_name == Benchmark.NEWSCRAWL.value:
            example_generator = JsonBenchmarkExampleReader(settings.BENCHMARK_DIR + "newscrawl.benchmark.jsonl")
        else:
            logger.info("Load mappings for example generator...")
            entity_db = EntityDatabase()
            entity_db.load_wikipedia_wikidata_mapping()
            entity_db.load_redirects()
            logger.info("-> Mappings loaded.")
            if benchmark_name == Benchmark.ACE.value:
                example_generator = XMLExampleReader(entity_db,
                                                     settings.ACE04_BENCHMARK_LABELS,
                                                     settings.ACE04_BENCHMARK_TEXTS)
            elif benchmark_name == Benchmark.MSNBC_UPDATED.value:
                example_generator = XMLExampleReader(entity_db,
                                                     settings.MSNBC_BENCHMARK_LABELS,
                                                     settings.MSNBC_BENCHMARK_TEXTS)
            elif benchmark_name == Benchmark.ACE_ORIGINAL.value:
                example_generator = XMLExampleReader(entity_db,
                                                     settings.ACE04_ORIGINAL_BENCHMARK_LABELS,
                                                     settings.ACE04_ORIGINAL_BENCHMARK_TEXTS)
            elif benchmark_name == Benchmark.MSNBC_ORIGINAL.value:
                example_generator = XMLExampleReader(entity_db,
                                                     settings.MSNBC_ORIGINAL_BENCHMARK_LABELS,
                                                     settings.MSNBC_ORIGINAL_BENCHMARK_TEXTS)
            elif benchmark_name == Benchmark.WIKIPEDIA.value:
                example_generator = WikipediaExampleReader(entity_db)
            elif benchmark_name in [Benchmark.AIDA_CONLL.value, Benchmark.AIDA_CONLL_TRAIN.value, Benchmark.AIDA_CONLL_DEV.value,
                                    Benchmark.AIDA_CONLL_TEST.value]:
                example_generator = AidaConllExampleReader(entity_db, settings.AIDA_CONLL_BENCHMARK_FILE, benchmark_name)
            else:
                raise ValueError("%s is not a known benchmark." % benchmark_name)
    return example_generator
