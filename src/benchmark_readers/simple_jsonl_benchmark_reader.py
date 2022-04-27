from typing import Iterator

from src.evaluation.groundtruth_label import GroundtruthLabel
from src.models.article import Article
from src.models.entity_database import EntityDatabase

import os
import json
import logging

from src.utils.knowledge_base_mapper import KnowledgeBaseMapper
from src.utils.nested_groundtruth_handler import NestedGroundtruthHandler

logger = logging.getLogger("main." + __name__.split(".")[-1])


class SimpleJsonlBenchmarkReader:
    def __init__(self, entity_db: EntityDatabase):
        self.entity_db = entity_db
        self.article_id_counter = 0

    def get_articles_from_file(self, filepath: str) -> Iterator[Article]:
        """
        Yields all articles with their GT labels from the given file.
        """
        with open(filepath, "r", encoding="utf8") as file:
            for line in file:
                label_id_counter = 0
                no_mapping_count = 0
                benchmark_json = json.loads(line)
                title = benchmark_json["title"] if "title" in benchmark_json else ""
                text = benchmark_json["text"]
                labels = []
                for raw_label in benchmark_json["labels"]:
                    span = raw_label["start_char"], raw_label["end_char"]
                    entity_uri = raw_label["entity_reference"]
                    entity_id = KnowledgeBaseMapper.get_wikidata_qid(entity_uri, self.entity_db, verbose=False)
                    if not entity_id:
                        no_mapping_count += 1
                        entity_id = "Unknown"
                        entity_name = "UnknownNoMapping"
                    else:
                        # The name for the GT label is Unknown for now, but is added when creating a benchmark in our
                        # format
                        entity_name = "Unknown"

                    labels.append(GroundtruthLabel(label_id_counter, span, entity_id, entity_name))
                    label_id_counter += 1

                # Assign parent and child ids to GT labels in case of nested GT labels
                NestedGroundtruthHandler.assign_parent_and_child_ids(labels)

                article = Article(id=self.article_id_counter, title=title, text=text, labels=labels)
                self.article_id_counter += 1

                if no_mapping_count > 0:
                    logger.warning("%d Labels could not be mapped to any Wikidata QID." % no_mapping_count)

                yield article

    def article_iterator(self, benchmark_path: str) -> Iterator[Article]:
        """
        Yields for each document in the NIF file or directory with NIF files
        a article with labels.
        """
        # Reset article ID counter
        self.article_id_counter = 0

        if os.path.isdir(benchmark_path):
            for filename in sorted(os.listdir(benchmark_path)):
                file_path = os.path.join(benchmark_path, filename)
                articles = self.get_articles_from_file(file_path)
                for article in articles:
                    yield article
        else:
            articles = self.get_articles_from_file(benchmark_path)
            for article in articles:
                yield article
