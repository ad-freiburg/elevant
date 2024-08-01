import logging

from typing import Iterator, Dict, Tuple

from elevant.models.article import Article
from elevant.models.entity_prediction import EntityPrediction
from elevant.prediction_readers.abstract_prediction_reader import AbstractPredictionReader
from elevant import settings

logger = logging.getLogger("main." + __name__.split(".")[-1])

LABEL_COLUMN = 5
TOKEN_COLUMN = 0
IOB_COLUMN = 4
SPAN_COLUMN = 1


class MaterialELPredictionReader(AbstractPredictionReader):
    def __init__(self, input_filepath: str, has_iob_tags=True):
        self.input_filepath = input_filepath
        self.has_iob_tags = has_iob_tags

        # Set article variables
        self._reset_article_variables()

        self.abbrev_uri_mapping = {}
        self.label_uri_mapping = {}
        with open(settings.CUSTOM_TAGS_FILE, "r", encoding="utf8") as file:
            for line in file:
                abbrev, label, uri = line.strip("\n").split("\t")
                self.abbrev_uri_mapping[abbrev] = uri
                self.label_uri_mapping[label] = uri

        super().__init__(input_filepath, predictions_iterator_implemented=True)

    def _reset_article_variables(self):
        self.curr_text = ""
        self.curr_labels = []
        self.curr_span_start = 0
        self.curr_span_end_original = -1
        self.curr_entity_id = None
        self.curr_entity_name = None

    def _get_label(self):
        span = (self.curr_span_start, len(self.curr_text))
        # The name for the GT label is Unknown for now, but is added when creating a benchmark in our format
        label = EntityPrediction(span, self.curr_entity_id, {self.curr_entity_id})

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
                        yield {prediction.span: prediction for prediction in self.curr_labels}
                        article_id_counter += 1
                    self._reset_article_variables()
                else:
                    token = lst[TOKEN_COLUMN]

                    if not self.has_iob_tags:
                        label = lst[LABEL_COLUMN]
                        print(f"Label: {label}, curr_entity_id: {self.curr_entity_id}")
                        if self.curr_entity_id and (label == "O" or self.label_uri_mapping[label] != self.curr_entity_id):
                            self.curr_labels.append(self._get_label())
                        self.curr_text += " "
                        if label != "O" and self.label_uri_mapping[label] != self.curr_entity_id:
                            self.curr_span_start = len(self.curr_text)
                            self.curr_entity_name = "Unknown"
                            self.curr_entity_id = self.label_uri_mapping[label]
                    else:
                        iob_tag = lst[IOB_COLUMN]
                        if self.curr_entity_id and (iob_tag.startswith("B") or iob_tag.startswith("O")):
                            self.curr_labels.append(self._get_label())

                        # original_span_start, original_span_end = lst[1].split("-")
                        # original_span_start, original_span_end = int(original_span_start), int(original_span_end)
                        # self.last_span_end_original = self.curr_span_end_original
                        # self.curr_span_end_original = original_span_end
                        # if self.last_span_end_original > 0 and self.last_span_end_original != original_span_start:
                        self.curr_text += " "

                        if iob_tag.startswith("B"):
                            abbrev = iob_tag[2:]

                            # IOB token is "B" therefore set current span start
                            self.curr_span_start = len(self.curr_text)
                            self.curr_entity_name = "Unknown"
                            self.curr_entity_id = self.abbrev_uri_mapping[abbrev]

                    # Add current token to text and append whitespace
                    self.curr_text += token

        # Add last GT label and article
        if self.curr_entity_id:
            # Add GT label directly preceding the last empty lines of the file
            self.curr_labels.append(self._get_label())
        if self.curr_text:
            yield {prediction.span: prediction for prediction in self.curr_labels}

    def predictions_iterator(self) -> Iterator[Dict[Tuple[int, int], EntityPrediction]]:
        for i, predictions in enumerate(self.get_articles_from_file(self.input_filepath)):
            yield predictions
