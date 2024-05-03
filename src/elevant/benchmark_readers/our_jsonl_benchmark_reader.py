import logging
from typing import Iterator

from elevant.benchmark_readers.abstract_benchmark_reader import AbstractBenchmarkReader
from elevant.models.article import Article, article_from_json

logger = logging.getLogger("main." + __name__.split(".")[-1])


class OurJsonlBenchmarkReader(AbstractBenchmarkReader):
    def __init__(self, benchmark_filename: str):
        self.benchmark_filename = benchmark_filename

    def article_iterator(self) -> Iterator[Article]:
        with open(self.benchmark_filename, "r") as benchmark_file:
            for i, json_line in enumerate(benchmark_file):
                article = article_from_json(json_line)
                if i == 0 and "aida-conll" in self.benchmark_filename and article.text.count("*") > 20:
                    logger.warning("The AIDA-CoNLL benchmark texts are obscured in ELEVANT for license reasons. "
                                   "Make sure the task you're executing does not depend on the benchmark text "
                                   "or get your own copy of the AIDA-CoNLL benchmark and add it to ELEVANT as "
                                   "described in docs/add_benchmark.md.")
                yield article
