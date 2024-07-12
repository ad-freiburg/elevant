import os
import logging

from typing import Iterator, Dict

from pynif import NIFCollection
from rdflib import Graph

from elevant.benchmark_readers.abstract_benchmark_reader import AbstractBenchmarkReader
from elevant.evaluation.groundtruth_label import GroundtruthLabel
from elevant.models.entity_database import EntityDatabase
from elevant.models.article import Article
from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper, UnknownEntity
from elevant.utils.nested_groundtruth_handler import NestedGroundtruthHandler

logger = logging.getLogger("main." + __name__.split(".")[-1])


class OkeBenchmarkReader(AbstractBenchmarkReader):
    """
    OKE benchmarks come in the ttl format. They can however not be parsed using
    the NIF benchmark reader, since the taIdentRef of a mention is not the
    actual entity URI, but rather the sameAs relation is used to map
    taIdentRefs to the DBpedia URI.
    Therefore the OKE benchmark reader first generates a dictionary that maps
    all taIdentRefs to their DBpedia URI using the sameAs relation. This
    dictionary is then used during parsing to map taIdentRefs to the correct
    entity URI which can then be mapped to a Wikidata QID using the
    KnowledgeBaseMapper.
    """
    def __init__(self, entity_db: EntityDatabase, benchmark_path: str):
        self.entity_db = entity_db
        self.benchmark_path = benchmark_path
        self.article_id_counter = 0

    def get_articles_from_nif(self, nif_content: str, same_as_mapping: Dict[str, str]) -> Iterator[Article]:
        """
        Create articles from the given NIF content.
        """
        nif_doc = NIFCollection.loads(nif_content)

        no_mapping_count = 0

        # NIF contexts have random order by default. Make sure results are reproducible by sorting by URI
        for context in sorted(nif_doc.contexts, key=lambda c: c.uri):
            label_id_counter = 0
            text = context.mention
            if not text:
                # This happens e.g. in KORE50 for the parent context
                # <http://www.mpi-inf.mpg.de/yago-naga/aida/download/KORE50.tar.gz/AIDA.tsv>
                continue
            title = context.uri
            labels = []
            # Make sure annotations are sorted by start index
            for phrase in sorted(context.phrases, key=lambda p: p.beginIndex):
                span = phrase.beginIndex, phrase.endIndex
                entity_uri = phrase.taIdentRef
                entity_id = UnknownEntity.NIL.value
                if entity_uri in same_as_mapping:
                    entity_uri = same_as_mapping[entity_uri]
                    entity_id = KnowledgeBaseMapper.get_wikidata_qid(entity_uri, self.entity_db, verbose=True)

                if KnowledgeBaseMapper.is_unknown_entity(entity_id):
                    no_mapping_count += 1

                # The name for the GT label is Unknown for now, but is added when creating a benchmark in our format
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

    @staticmethod
    def get_same_as_mappings(filepath: str) -> Dict[str, str]:
        """
        Retrieve the sameAs mapping from the turtle file.
        """
        same_as_mapping = {}
        graph = Graph()
        graph.parse(filepath, format='ttl')
        for subj, pred, obj in graph:
            subj, pred, obj = str(subj), str(pred), str(obj)
            if pred == "http://www.w3.org/2002/07/owl#sameAs":
                same_as_mapping[subj] = obj
        return same_as_mapping

    def get_articles_from_file(self, filepath: str) -> Iterator[Article]:
        """
        Yields all articles with their GT labels from the given file.
        """
        same_as_mapping = self.get_same_as_mappings(filepath)
        with open(filepath, "r", encoding="utf8") as file:
            file_content = file.readlines()
            file_content = "".join(file_content)
            for article in self.get_articles_from_nif(file_content, same_as_mapping):
                yield article

    def article_iterator(self) -> Iterator[Article]:
        """
        Yields for each document in the NIF file or directory with NIF files
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
