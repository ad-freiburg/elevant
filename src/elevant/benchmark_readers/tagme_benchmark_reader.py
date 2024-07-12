from typing import Iterator

from elevant.benchmark_readers.abstract_benchmark_reader import AbstractBenchmarkReader
from elevant.evaluation.groundtruth_label import GroundtruthLabel
from elevant.models.article import Article
from elevant.models.entity_database import EntityDatabase

import logging

from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper, UnknownEntity
from elevant.utils.nested_groundtruth_handler import NestedGroundtruthHandler

logger = logging.getLogger("main." + __name__.split(".")[-1])


class TagmeBenchmarkReader(AbstractBenchmarkReader):
    def __init__(self, entity_db: EntityDatabase, annotation_path: str, snippet_path: str):
        self.entity_db = entity_db
        self.snippet_path = snippet_path
        self.annotation_path = annotation_path
        self.article_id_counter = 0

    def get_articles_from_files(self, snippet_path: str, annotation_path: str) -> Iterator[Article]:
        """
        Yields all articles with their GT labels from the given files.
        """
        no_mapping_count = 0
        overlapping_gt_count = 0
        no_wikipedia_title_count = 0

        snippet_file = open(snippet_path, "r", encoding="utf8")
        annotation_file = open(annotation_path, "r", encoding="utf8")

        article_id = -1
        mention_text = ""
        wikipedia_id = -1

        for line in snippet_file:
            label_id_counter = 0
            line_id, text = line.strip("\n").split("\t")
            line_id = int(line_id)
            labels = []
            label_dict = {}

            while True:
                if article_id == line_id:
                    mention_start = text.lower().find(mention_text)
                    if mention_start > -1:
                        span = mention_start, mention_start + len(mention_text)
                        wikipedia_title = self.entity_db.get_wikipedia_title_by_wikipedia_id(wikipedia_id)
                        if not wikipedia_title:
                            logger.info("No Wikipedia title found for Wikipedia ID %d" % wikipedia_id)
                            entity_id = UnknownEntity.NO_MAPPING.value
                            no_wikipedia_title_count += 1
                        else:
                            entity_id = KnowledgeBaseMapper.get_wikidata_qid(wikipedia_title, self.entity_db,
                                                                             verbose=False)
                        if KnowledgeBaseMapper.is_unknown_entity(entity_id):
                            no_mapping_count += 1

                        # The name for the GT label is Unknown for now, but is added when creating a benchmark in
                        # our format
                        entity_name = "Unknown"

                        labels.append(GroundtruthLabel(label_id_counter, span, entity_id, entity_name))
                        label_dict[label_id_counter] = mention_text
                        label_id_counter += 1
                    else:
                        logger.warning("Could not find mention text \"%s\" in text \"%s\"" % (mention_text, text))

                annotation_line = annotation_file.readline()
                if not annotation_line:
                    break
                article_id, mention_text, wikipedia_id = annotation_line.strip("\n").split("\t")
                article_id = int(article_id)
                wikipedia_id = int(wikipedia_id)
                if article_id > line_id:
                    break

            # Assign parent and child ids to GT labels in case of nested GT labels
            NestedGroundtruthHandler.assign_parent_and_child_ids(labels)
            for gt_label in labels:
                if gt_label.children:
                    logger.info("Overlapping GT mention for text \"%s\" %s in \"%s\""
                                % (text[gt_label.span[0]:gt_label.span[1]], label_dict[gt_label.children[0]], text))
                    overlapping_gt_count += 1

            article = Article(id=self.article_id_counter, title="", text=text, labels=labels)
            self.article_id_counter += 1

            yield article

        if no_mapping_count > 0:
            logger.info("%d entity names could not be mapped to any Wikidata QID (includes unknown entities)."
                        % no_mapping_count)

        logger.info("%d ground truth mentions are overlapping." % overlapping_gt_count)
        logger.info("%d wikipedia IDs could not be mapped to a Wikipedia title." % no_wikipedia_title_count)

        snippet_file.close()
        annotation_file.close()

    def article_iterator(self) -> Iterator[Article]:
        """
        Yields for each document in the TagMe benchmark files an article with labels.
        """
        # Reset article ID counter
        self.article_id_counter = 0

        articles = self.get_articles_from_files(self.snippet_path, self.annotation_path)
        for article in articles:
            yield article
