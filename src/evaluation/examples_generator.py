from typing import Iterator, Tuple, Optional

from src.evaluation.benchmark import Benchmark
from src.evaluation.groundtruth_label import GroundtruthLabel
from src.helpers.wikipedia_corpus import WikipediaCorpus
from src.models.wikipedia_article import WikipediaArticle
from src.models.entity_database import EntityDatabase
from src.models.conll_benchmark import conll_documents
from src.models.wikipedia_article import article_from_json
from src.helpers.xml_benchmark_reader import XMLBenchmarkParser
from src import settings

import operator
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

    def iterate(self, n: int = -1) -> Iterator[WikipediaArticle]:
        for article in WikipediaCorpus.development_articles(n):
            article.labels = []
            label_id_counter = 0
            for span, target in article.links:
                span = expand_span(article.text, span)
                entity_id = self.entity_db.link2id(target)
                if entity_id is None:
                    entity_id = "Unknown"
                gt_label = GroundtruthLabel(label_id_counter, span, entity_id, "Unknown")
                article.labels.append(gt_label)
                label_id_counter += 1
            yield article


class ConllExampleReader:
    @staticmethod
    def iterate(n: int = -1) -> Iterator[WikipediaArticle]:
        for i, document in enumerate(conll_documents()):
            if i == n:
                break
            article = document.to_article()
            yield article


class ConllDevExampleReader:
    @staticmethod
    def iterate(n: int = -1) -> Iterator[WikipediaArticle]:
        articles_count = 0
        for i, document in enumerate(conll_documents()):
            if i < 946:
                # Articles 1 to 946 belong to the training dataset
                continue
            if i >= 1162:
                # Articles 1163 to 1393 belong to the test dataset
                break
            if articles_count == n:
                break
            article = document.to_article()
            articles_count += 1
            yield article


class ConllTestExampleReader:
    @staticmethod
    def iterate(n: int = -1) -> Iterator[WikipediaArticle]:
        articles_count = 0
        for i, document in enumerate(conll_documents()):
            if i < 1162:
                # Articles < 1163 belong to the training and dev dataset
                continue
            if articles_count == n:
                break
            article = document.to_article()
            articles_count += 1
            yield article


class PseudoLinkConllExampleReader:
    def __init__(self, entity_db: EntityDatabase):
        self.entity_db = entity_db

    def iterate(self, n: int = -1) -> Iterator[WikipediaArticle]:
        for i, document in enumerate(conll_documents()):
            if i == n:
                break
            article = document.to_article()

            # Store first occurrence of each entity in the article
            unique_labels = dict()
            for gt_label in article.labels:
                label = gt_label.entity_id
                span = gt_label.span
                if label not in unique_labels:
                    unique_labels[label] = span
            unique_labels = sorted(unique_labels.items(), key=operator.itemgetter(1))

            # Select 60% of unique entities at random (with seed for reproducibility)
            n_pseudo_links = int(0.6 * len(unique_labels))
            random_indices = random.sample(range(len(unique_labels)), n_pseudo_links)
            random_indices = sorted(random_indices)  # links should be sorted

            # Generate pseudo links
            links = []
            for index in random_indices:
                entity_id, span = unique_labels[index]
                entity_name = self.entity_db.id2wikipedia_name(entity_id)
                links.append(((span[0], span[1]), entity_name))
            article.links = links
            yield article


class AceExampleReader:
    def __init__(self, entity_db: EntityDatabase):
        self.entity_db = entity_db

    def iterate(self, n: int = -1) -> Iterator[WikipediaArticle]:
        parser = XMLBenchmarkParser(self.entity_db)
        for i, article in enumerate(parser.article_iterator(settings.ACE04_BENCHMARK_LABELS,
                                                            settings.ACE04_BENCHMARK_TEXTS)):
            if i == n:
                break
            yield article


class MsnbcExampleReader:
    def __init__(self, entity_db: EntityDatabase):
        self.entity_db = entity_db

    def iterate(self, n: int = -1) -> Iterator[WikipediaArticle]:
        parser = XMLBenchmarkParser(self.entity_db)
        for i, article in enumerate(parser.article_iterator(settings.MSNBC_BENCHMARK_LABELS,
                                                            settings.MSNBC_BENCHMARK_TEXTS)):
            if i == n:
                break
            yield article


class JsonBenchmarkExampleReader:
    def __init__(self, benchmark_filename: str):
        self.benchmark_filename = benchmark_filename

    def iterate(self, n: int = -1) -> Iterator[WikipediaArticle]:
        with open(self.benchmark_filename, "r") as benchmark_file:
            for i, json_line in enumerate(benchmark_file):
                if i == n:
                    break
                article = article_from_json(json_line)
                yield article


def get_example_generator(benchmark_name: str, from_json_file: Optional[bool] = True):
    path = "benchmarks/"
    if from_json_file:
        if benchmark_name == Benchmark.WIKI_EX.value:
            benchmark_filename = path + "benchmark_labels_wiki-ex.jsonl"
        elif benchmark_name == Benchmark.CONLL_DEV.value:
            benchmark_filename = path + "benchmark_labels_conll-dev.jsonl"
        elif benchmark_name == Benchmark.CONLL_TEST.value:
            benchmark_filename = path + "benchmark_labels_conll-test.jsonl"
        elif benchmark_name == Benchmark.CONLL.value:
            benchmark_filename = path + "benchmark_labels_conll.jsonl"
        elif benchmark_name == Benchmark.ACE.value:
            benchmark_filename = path + "benchmark_labels_ace.jsonl"
        elif benchmark_name == Benchmark.MSNBC.value:
            benchmark_filename = path + "benchmark_labels_msnbc.jsonl"
        elif benchmark_name == Benchmark.NEWSCRAWL.value:
            benchmark_filename = path + "benchmark_labels_newscrawl.jsonl"
        else:
            raise ValueError("%s is not a known benchmark." % benchmark_name)
        example_generator = JsonBenchmarkExampleReader(benchmark_filename)
    else:
        if benchmark_name == Benchmark.CONLL.value:
            example_generator = ConllExampleReader()
        elif benchmark_name == Benchmark.CONLL_DEV.value:
            example_generator = ConllDevExampleReader()
        elif benchmark_name == Benchmark.CONLL_TEST.value:
            example_generator = ConllTestExampleReader()
        elif benchmark_name == Benchmark.WIKI_EX.value:
            example_generator = JsonBenchmarkExampleReader(settings.WIKI_EX_BENCHMARK_FILE)
        elif benchmark_name == Benchmark.NEWSCRAWL.value:
            example_generator = JsonBenchmarkExampleReader(path + "benchmark_labels_newscrawl.jsonl")
        else:
            logger.info("Load mappings for example generator...")
            entity_db = EntityDatabase()
            entity_db.load_wikipedia_wikidata_mapping()
            entity_db.load_redirects()
            logger.info("-> Mappings loaded.")
            if benchmark_name == Benchmark.ACE.value:
                example_generator = AceExampleReader(entity_db)
            elif benchmark_name == Benchmark.MSNBC.value:
                example_generator = MsnbcExampleReader(entity_db)
            elif benchmark_name == Benchmark.CONLL_PSEUDO_LINKS.value:
                example_generator = PseudoLinkConllExampleReader(entity_db)
            elif benchmark_name == Benchmark.WIKIPEDIA.value:
                example_generator = WikipediaExampleReader(entity_db)
            else:
                raise ValueError("%s is not a known benchmark." % benchmark_name)
    return example_generator
