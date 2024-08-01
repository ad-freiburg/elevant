import logging

from typing import Iterator

from elevant.benchmark_readers.abstract_benchmark_reader import AbstractBenchmarkReader
from elevant.evaluation.groundtruth_label import GroundtruthLabel
from elevant.models.article import Article
from elevant.utils.nested_groundtruth_handler import NestedGroundtruthHandler
from elevant import settings

logger = logging.getLogger("main." + __name__.split(".")[-1])

TOKEN_COLUMN = 0
IOB_COLUMN = 1
SPAN_COLUMN = 1


class MaterialELBenchmarkReader(AbstractBenchmarkReader):
    def __init__(self, benchmark_path: str):
        self.benchmark_path = benchmark_path

        # Set article variables
        self._reset_article_variables()

        self.abbrev_uri_mapping = {}
        with open(settings.CUSTOM_TAGS_FILE, "r", encoding="utf8") as file:
            for line in file:
                abbrev, label, uri = line.strip("\n").split("\t")
                self.abbrev_uri_mapping[abbrev] = uri

    def _reset_article_variables(self):
        self.curr_text = ""
        self.curr_labels = []
        self.label_id_counter = 0
        self.curr_span_start = 0
        self.curr_span_end_original = -1
        self.curr_entity_id = None
        self.curr_entity_name = None

    def _get_article(self, article_id_counter):
        # Strip last trailing whitespace
        self.curr_text = self.curr_text

        # Assign parent and child ids to GT labels in case of nested GT labels
        NestedGroundtruthHandler.assign_parent_and_child_ids(self.curr_labels)

        return Article(article_id_counter, title="", text=self.curr_text, labels=self.curr_labels)

    def _get_label(self):
        span = (self.curr_span_start, len(self.curr_text))
        # The name for the GT label is Unknown for now, but is added when creating a benchmark in our format
        label = GroundtruthLabel(self.label_id_counter, span, self.curr_entity_id, self.curr_entity_name)
        self.label_id_counter += 1
        self.curr_entity_id = None
        return label

    def get_articles_from_file(self, benchmark_path: str) -> Iterator[Article]:
        article_id_counter = 0
        with open(benchmark_path, "r", encoding="utf8") as file:
            self._reset_article_variables()
            for i, line in enumerate(file):
                if i == 0:
                    # First line contains column headers
                    continue
                lst = line.strip("\n").split("\t")
                if not lst[0]:
                    # Begin of a new article (have one "article" per sentence)
                    if self.curr_text:
                        if self.curr_entity_id:
                            # Add GT label directly preceding the empty line before the next article
                            self.curr_labels.append(self._get_label())
                        yield self._get_article(article_id_counter)
                        article_id_counter += 1
                    self._reset_article_variables()
                else:
                    token = lst[TOKEN_COLUMN]
                    iob_tag = lst[IOB_COLUMN]

                    if self.curr_entity_id and (iob_tag.startswith("B") or iob_tag.startswith("O")):
                        self.curr_labels.append(self._get_label())

                    # Without BIO tags, this part should be commented out until the next comment
                    # original_span_start, original_span_end = lst[SPAN_COLUMN].split("-")
                    # original_span_start, original_span_end = int(original_span_start), int(original_span_end)
                    # self.last_span_end_original = self.curr_span_end_original
                    # self.curr_span_end_original = original_span_end
                    # if self.last_span_end_original > 0 and self.last_span_end_original != original_span_start:
                        # Without BIO tags, the previous part should be commented out
                    self.curr_text += " "

                    if iob_tag.startswith("B"):
                        label = iob_tag[2:]

                        # IOB token is "B" therefore set current span start
                        self.curr_span_start = len(self.curr_text)
                        self.curr_entity_name = "Unknown"
                        self.curr_entity_id = self.abbrev_uri_mapping[label]

                    # Add current token to text and append whitespace
                    self.curr_text += token

        # Add last GT label and article
        if self.curr_entity_id:
            # Add GT label directly preceding the last empty lines of the file
            self.curr_labels.append(self._get_label())
        if self.curr_text:
            yield self._get_article(article_id_counter)

    def article_iterator(self) -> Iterator[Article]:
        """
        Yields Article with labels for the benchmark_path and benchmark name.
        """
        articles = self.get_articles_from_file(self.benchmark_path)
        for i, article in enumerate(articles):
            yield article
