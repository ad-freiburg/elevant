import os
import logging
import re

from typing import Iterator, List

from pynif import NIFCollection
from urllib.parse import unquote

from src.evaluation.groundtruth_label import GroundtruthLabel
from src.models.entity_database import EntityDatabase
from src.models.article import Article


logger = logging.getLogger("main." + __name__.split(".")[-1])


class NifBenchmarkReader:
    def __init__(self, entity_db: EntityDatabase):
        self.entity_db = entity_db
        self.article_id_counter = 0

    @staticmethod
    def has_children(curr_label_idx: int, gt_labels: List[GroundtruthLabel]):
        child_indices = []
        curr_span = gt_labels[curr_label_idx].span
        for i, gt_label in enumerate(gt_labels):
            if gt_label.span[0] >= curr_span[0] and gt_label.span[1] <= curr_span[1] and curr_label_idx != i:
                child_indices.append(i)
        return child_indices

    def get_articles_from_nif(self, nif_content: str) -> Iterator[Article]:
        """
        Create WikipediaArticles from the given NIF content.
        """
        nif_doc = NIFCollection.loads(nif_content)

        # NIF contexts have random order by default. Make sure results are reproducible by sorting by URI
        for context in sorted(nif_doc.contexts, key=lambda c: c.uri):
            no_mapping_count = 0
            label_id_counter = 0
            text = context.mention
            if not text:
                # This happens e.g. in KORE50 for the parent context
                # <http://www.mpi-inf.mpg.de/yago-naga/aida/download/KORE50.tar.gz/AIDA.tsv>
                continue
            title = context.uri
            labels = []
            for phrase in context.phrases:
                span = phrase.beginIndex, phrase.endIndex
                entity_uri = phrase.taIdentRef
                entity_name = entity_uri[entity_uri.rfind("/") + 1:]
                # The GT label entity ID will be None if the provided entity ID
                # is not a QID or cannot be mapped from Wikipedia title to QID
                if entity_name and not re.match(r"Q[0-9]+", entity_name):
                    entity_name = unquote(entity_name).replace('_', ' ')
                    entity_id = self.entity_db.link2id(entity_name)
                    if not entity_id:
                        logger.warning("Entity name %s could not be mapped to a Wikidata ID." % entity_name)
                        no_mapping_count += 1
                        entity_id = "Unknown"
                        entity_name = "UnknownNoMapping"
                    else:
                        entity_name = "Unknown"
                else:
                    entity_id = entity_name if entity_name else "Unknown"
                    entity_name = "Unknown"

                # The name for the GT label is Unknown for now, but is added when creating a benchmark in our format
                labels.append(GroundtruthLabel(label_id_counter, span, entity_id, entity_name))
                label_id_counter += 1

            # Assign parent and child ids to GT labels in case of nested GT labels
            for i, gt_label in enumerate(labels):
                child_indices = self.has_children(i, labels)
                for child_idx in child_indices:
                    child_gt_label = labels[child_idx]
                    child_gt_label.parent = gt_label.id
                    gt_label.children.append(child_gt_label.id)

            article = Article(id=self.article_id_counter, title=title, text=text, links=[], labels=labels)
            self.article_id_counter += 1

            if no_mapping_count > 0:
                logger.warning("%d Labels could not be matched to any Wikidata ID." % no_mapping_count)

            yield article

    def get_articles_from_file(self, filepath: str) -> Iterator[Article]:
        """
        Yields all WikipediaArticles with their GT labels from the given file.
        """
        with open(filepath, "r", encoding="utf8") as file:
            file_content = file.readlines()
            file_content = "".join(file_content)
            for article in self.get_articles_from_nif(file_content):
                yield article

    def article_iterator(self, benchmark_path: str) -> Iterator[Article]:
        """
        Yields for each document in the NIF file or directory with NIF files
        a WikipediaArticle with labels.
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
