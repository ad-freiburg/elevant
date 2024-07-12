from typing import Iterator, Optional

from elevant.benchmark_readers.abstract_benchmark_reader import AbstractBenchmarkReader
from elevant.evaluation.groundtruth_label import GroundtruthLabel
from elevant.models.article import Article
from elevant.models.entity_database import EntityDatabase

import os
import json
import logging

from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper, UnknownEntity
from elevant.utils.nested_groundtruth_handler import NestedGroundtruthHandler

logger = logging.getLogger("main." + __name__.split(".")[-1])


class SimpleJsonlBenchmarkReader(AbstractBenchmarkReader):
    def __init__(self, entity_db: EntityDatabase, benchmark_path: str, custom_kb: Optional[bool] = False):
        self.entity_db = entity_db
        self.benchmark_path = benchmark_path
        self.article_id_counter = 0
        self.custom_kb = custom_kb

    def get_articles_from_file(self, filepath: str) -> Iterator[Article]:
        """
        Yields all articles with their GT labels from the given file.
        """
        no_mapping_count = 0

        with open(filepath, "r", encoding="utf8") as file:
            for line in file:
                label_id_counter = 0
                benchmark_json = json.loads(line)
                title = benchmark_json["title"] if "title" in benchmark_json else ""
                text = benchmark_json["text"]
                labels = []
                for raw_label in sorted(benchmark_json["labels"], key=lambda x: x["start_char"]):
                    span = raw_label["start_char"], raw_label["end_char"]
                    entity_uri = raw_label["entity_reference"]
                    coref = raw_label["coref"] if "coref" in raw_label else None
                    if self.custom_kb:
                        entity_id = entity_uri if entity_uri else UnknownEntity.NIL.value
                    else:
                        entity_id = KnowledgeBaseMapper.get_wikidata_qid(entity_uri, self.entity_db, verbose=False)

                    if KnowledgeBaseMapper.is_unknown_entity(entity_id):
                        no_mapping_count += 1

                    # The name for the GT label is Unknown for now, but is added when creating a benchmark in our
                    # format
                    entity_name = "Unknown"

                    labels.append(GroundtruthLabel(label_id_counter, span, entity_id, entity_name, coref=coref))
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
        Yields for each document in the simple-jsonl file or directory with simple-jsonl files
        an article with labels.
        """
        # Reset article ID counter
        self.article_id_counter = 0

        if os.path.isdir(self.benchmark_path):
            for filename in sorted(os.listdir(self.benchmark_path)):
                file_path = os.path.join(self.benchmark_path, filename)
                articles = self.get_articles_from_file(file_path)
                for article in articles:
                    yield article
        else:
            articles = self.get_articles_from_file(self.benchmark_path)
            for article in articles:
                yield article
