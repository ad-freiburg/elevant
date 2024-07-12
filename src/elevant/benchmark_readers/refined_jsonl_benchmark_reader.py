from typing import Iterator

from elevant.benchmark_readers.abstract_benchmark_reader import AbstractBenchmarkReader
from elevant.evaluation.groundtruth_label import GroundtruthLabel
from elevant.models.article import Article
from elevant.models.entity_database import EntityDatabase

import json
import logging

from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper
from elevant.utils.nested_groundtruth_handler import NestedGroundtruthHandler

logger = logging.getLogger("main." + __name__.split(".")[-1])


class RefinedJsonlBenchmarkReader(AbstractBenchmarkReader):
    def __init__(self, entity_db: EntityDatabase, benchmark_path: str):
        self.entity_db = entity_db
        self.benchmark_path = benchmark_path
        self.article_id_counter = 0

    def get_articles_from_file(self, filepath: str) -> Iterator[Article]:
        """
        Yields all articles with their GT labels from the given file.
        """
        no_mapping_count = 0

        with open(filepath, "r", encoding="utf8") as file:
            for line in file:
                label_id_counter = 0
                benchmark_json = json.loads(line)
                title = benchmark_json["doc_title"] if "doc_title" in benchmark_json else ""
                text = benchmark_json["text"]
                labels = []
                for raw_label in benchmark_json["mentions"]:
                    start = raw_label["start"]
                    length = raw_label["length"]
                    span = start, start + length
                    entity_reference = raw_label["wiki_name"]
                    entity_id = KnowledgeBaseMapper.get_wikidata_qid(entity_reference, self.entity_db, verbose=False)

                    if KnowledgeBaseMapper.is_unknown_entity(entity_id):
                        no_mapping_count += 1

                    # The name for the GT label is Unknown for now, but is added when creating a benchmark in our
                    # format
                    entity_name = "Unknown"

                    labels.append(GroundtruthLabel(label_id_counter, span, entity_id, entity_name))
                    label_id_counter += 1

                # Assign parent and child ids to GT labels in case of nested GT labels
                NestedGroundtruthHandler.assign_parent_and_child_ids(labels)

                article = Article(id=self.article_id_counter, title=title, text=text, labels=labels)
                self.article_id_counter += 1

                yield article

        if no_mapping_count > 0:
            logger.info("%d entity names could not be mapped to any Wikidata QID (includes unknown entities)."
                        % no_mapping_count)

    def article_iterator(self) -> Iterator[Article]:
        """
        Yields for each document in the refined-json file an article with labels.
        """
        # Reset article ID counter
        self.article_id_counter = 0
        articles = self.get_articles_from_file(self.benchmark_path)
        for article in articles:
            yield article
