from typing import Iterator

from elevant.benchmark_readers.abstract_benchmark_reader import AbstractBenchmarkReader
from elevant.evaluation.groundtruth_label import GroundtruthLabel
from elevant.models.article import Article
from elevant.models.entity_database import EntityDatabase

import logging

from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper
from elevant.utils.nested_groundtruth_handler import NestedGroundtruthHandler

logger = logging.getLogger("main." + __name__.split(".")[-1])


class TsvBenchmarkReader(AbstractBenchmarkReader):
    def __init__(self, entity_db: EntityDatabase, benchmark_path: str):
        self.entity_db = entity_db
        self.benchmark_path = benchmark_path
        self.article_id_counter = 0

    def get_articles_from_file(self, filepath: str) -> Iterator[Article]:
        """
        Yields all articles with their GT labels from the given file.
        """
        def create_article(article_id, text, labels):
            """
            Create and return an article from the given article ID, text and labels
            """
            # Assign parent and child ids to GT labels in case of nested GT labels
            NestedGroundtruthHandler.assign_parent_and_child_ids(labels)
            return Article(id=article_id, title="", text=text.strip(), labels=labels)

        no_mapping_count = 0
        label_id_counter = 0
        text = ""
        labels = []
        with open(filepath, "r", encoding="utf8") as file:
            for line in file:
                line = line.strip()

                if not line:
                    # An empty line indicates a new document, so yield the most recent article
                    yield create_article(self.article_id_counter, text, labels)

                    # Reset / update article values
                    self.article_id_counter += 1
                    label_id_counter = 0
                    text = ""
                    labels = []
                    continue

                lst = line.split("\t")
                token = lst[0]
                entity_reference = lst[1]
                ner_iob = lst[2][0]

                start_idx = len(text)
                text += token + " "
                end_idx = len(text) - 1

                if ner_iob == "B":
                    # Add a ground truth label
                    span = start_idx, end_idx
                    entity_id = KnowledgeBaseMapper.get_wikidata_qid(entity_reference, self.entity_db, verbose=False)
                    if KnowledgeBaseMapper.is_unknown_entity(entity_id):
                        no_mapping_count += 1

                    # The name for the GT label is Unknown for now, but is added when creating a benchmark in our
                    # format
                    entity_name = "Unknown"

                    labels.append(GroundtruthLabel(label_id_counter, span, entity_id, entity_name))
                    label_id_counter += 1
                elif ner_iob == "I":
                    # The previously added ground truth label was not finished, therefore adjust the span
                    labels[-1].span = labels[-1].span[0], end_idx

        if text:
            # Yield remaining article
            yield create_article(self.article_id_counter, text, labels)

        if no_mapping_count > 0:
            logger.info("%d entity names could not be mapped to any Wikidata QID (includes unknown entities)."
                        % no_mapping_count)

    def article_iterator(self) -> Iterator[Article]:
        """
        Yields for each document in the tsv file an article with labels.
        """
        # Reset article ID counter
        self.article_id_counter = 0
        articles = self.get_articles_from_file(self.benchmark_path)
        for article in articles:
            yield article
