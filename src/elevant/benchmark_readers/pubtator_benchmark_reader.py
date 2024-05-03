from typing import Iterator

from elevant.benchmark_readers.abstract_benchmark_reader import AbstractBenchmarkReader
from elevant.evaluation.groundtruth_label import GroundtruthLabel
from elevant.models.article import Article

import logging

from elevant.utils.nested_groundtruth_handler import NestedGroundtruthHandler

logger = logging.getLogger("main." + __name__.split(".")[-1])


class PubtatorBenchmarkReader(AbstractBenchmarkReader):
    def __init__(self, benchmark_path: str):
        self.benchmark_path = benchmark_path

    def get_articles_from_file(self, filepath: str) -> Iterator[Article]:
        """
        Yields all articles with their GT labels from the given file.
        """
        no_mapping_count = 0
        article_line_counter = 0
        title_len = 0
        text = ""
        title = ""
        article_id = -1
        labels = []
        label_id_counter = 0
        with open(filepath, "r", encoding="utf8") as file:
            for line in file:
                if line == "\n":
                    # Save previous article
                    # Assign parent and child ids to GT labels in case of nested GT labels
                    NestedGroundtruthHandler.assign_parent_and_child_ids(labels)
                    article = Article(id=article_id, title=title, text=text, labels=labels)
                    yield article

                    # Start next article
                    article_line_counter = 0
                    label_id_counter = 0
                    text = ""
                    labels = []
                    continue

                if article_line_counter == 0:
                    article_id, _, title = line.strip("\n").split("|")
                    text += title + "\n"
                elif article_line_counter == 1:
                    _, _, abstract = line.strip("\n").split("|")
                    text += abstract
                else:
                    _, start, end, _, _, entity_id = line.strip("\n").split("\t")
                    span = int(start), int(end)
                    if ":" not in entity_id:
                        # Dirty hack. The entities that have the MESH prefix in the KB don't have it in the NCBI
                        # benchmark.
                        entity_id = "MESH:" + entity_id
                    labels.append(GroundtruthLabel(label_id_counter, span, entity_id, "Unknown"))
                    label_id_counter += 1

                article_line_counter += 1

        if no_mapping_count > 0:
            logger.info("%d entity names could not be mapped to any Wikidata QID (includes unknown entities)."
                        % no_mapping_count)

    def article_iterator(self) -> Iterator[Article]:
        """
        Yields for each document in the pubtator file an article with labels.
        """
        articles = self.get_articles_from_file(self.benchmark_path)
        for article in articles:
            yield article
