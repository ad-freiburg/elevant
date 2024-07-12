import logging

from typing import Iterator, Optional

from elevant.benchmark_readers.abstract_benchmark_reader import AbstractBenchmarkReader
from elevant.evaluation.benchmark import Benchmark
from elevant.evaluation.groundtruth_label import GroundtruthLabel
from elevant.models.entity_database import EntityDatabase
from elevant.models.article import Article
from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper, UnknownEntity
from elevant.utils.nested_groundtruth_handler import NestedGroundtruthHandler

logger = logging.getLogger("main." + __name__.split(".")[-1])


class AidaConllBenchmarkReader(AbstractBenchmarkReader):
    def __init__(self, entity_db: EntityDatabase, benchmark_path: str, benchmark: Optional[str] = None):
        self.entity_db = entity_db
        self.benchmark_path = benchmark_path
        self.benchmark = benchmark

        # Set article variables
        self._reset_article_variables()

    def _reset_article_variables(self):
        self.curr_text = ""
        self.curr_labels = []
        self.no_mapping_count = 0
        self.label_id_counter = 0
        self.curr_span_start = 0
        self.curr_entity_id = None
        self.curr_entity_name = None

    def _get_article(self, article_id_counter):
        # Strip last trailing whitespace
        self.curr_text = self.curr_text[:-1]

        # Assign parent and child ids to GT labels in case of nested GT labels
        NestedGroundtruthHandler.assign_parent_and_child_ids(self.curr_labels)

        return Article(article_id_counter, title="", text=self.curr_text, labels=self.curr_labels)

    def _get_gt_label(self):
        span = (self.curr_span_start, len(self.curr_text) - 1)  # -1 for the appended whitespace
        # The name for the GT label is Unknown for now, but is added when creating a benchmark in our format
        label = GroundtruthLabel(self.label_id_counter, span, self.curr_entity_id, self.curr_entity_name)
        self.label_id_counter += 1
        return label

    def get_articles_from_file(self, benchmark_path: str) -> Iterator[Article]:
        article_id_counter = 0
        with open(benchmark_path, "r", encoding="utf8") as file:
            self._reset_article_variables()
            for line in file:
                lst = line.strip().split("\t")
                token = lst[0]
                if token.startswith("-DOCSTART-"):
                    # Begin of a new article
                    if self.curr_text:
                        if self.curr_entity_id:
                            # Add GT label directly preceding the empty line before the next article
                            self.curr_labels.append(self._get_gt_label())
                        yield self._get_article(article_id_counter)
                        article_id_counter += 1
                    self._reset_article_variables()
                elif token:
                    if len(lst) > 1 and lst[1] != "O":
                        iob_tag = lst[1]
                        entity_name = lst[3]
                        if iob_tag == "B" and entity_name != "null":  # null seems to indicate a cont. of the prev label
                            # Token is the start of a GT label
                            if entity_name == "--NME--":
                                entity_id = UnknownEntity.NIL.value
                            else:
                                # Get entity name and ID for current label
                                entity_uri = lst[4]
                                entity_id = KnowledgeBaseMapper.get_wikidata_qid(entity_uri, self.entity_db,
                                                                                 verbose=False)
                                if KnowledgeBaseMapper.is_unknown_entity(entity_id):
                                    # For AIDA-CONLL, 43 labels can not be mapped to any Wikidata ID.
                                    self.no_mapping_count += 1

                            # The name for the GT label is Unknown for now, but is added when creating a
                            # benchmark in our format
                            entity_name = "Unknown"

                            if self.curr_entity_id:
                                # Add GT label directly preceding the current one
                                self.curr_labels.append(self._get_gt_label())

                            # IOB token is "B" therefore set current span start
                            self.curr_span_start = len(self.curr_text)

                            self.curr_entity_name = entity_name
                            self.curr_entity_id = entity_id
                    elif self.curr_entity_id:
                        # Add GT label preceding the current token
                        self.curr_labels.append(self._get_gt_label())
                        self.curr_entity_id = None
                        self.curr_entity_name = None

                    # Add current token to text and append whitespace
                    self.curr_text += token + " "

        # Add last GT label and article
        if self.curr_entity_id:
            # Add GT label directly preceding the last empty lines of the file
            self.curr_labels.append(self._get_gt_label())
        if self.curr_text:
            yield self._get_article(article_id_counter)

    def article_iterator(self) -> Iterator[Article]:
        """
        Yields Article with labels for the benchmark_path and benchmark name.
        """
        articles = self.get_articles_from_file(self.benchmark_path)

        if self.benchmark == Benchmark.AIDA_CONLL_TRAIN.value:
            split_span = [0, 945]
        elif self.benchmark == Benchmark.AIDA_CONLL_DEV.value:
            split_span = [946, 1161]
        elif self.benchmark == Benchmark.AIDA_CONLL_TEST.value:
            split_span = [1162, 1392]
        else:
            split_span = [0, float('inf')]

        for i, article in enumerate(articles):
            if i < split_span[0]:
                continue
            if i > split_span[1]:
                break
            yield article
