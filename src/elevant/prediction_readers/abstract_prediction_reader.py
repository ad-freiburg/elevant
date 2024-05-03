from typing import Dict, Tuple, Iterator, List, Optional

import os
import logging

from elevant.models.article import Article
from elevant.models.entity_prediction import EntityPrediction

logger = logging.getLogger("main." + __name__.split(".")[-1])


def uppercase_predictions(predictions: Dict[Tuple[int, int], EntityPrediction],
                          text: str) -> Dict[Tuple[int, int], EntityPrediction]:
    filtered_predictions = {}
    for span in predictions:
        entity_prediction = predictions[span]
        begin, end = entity_prediction.span
        snippet = text[begin:end]
        if any([char.isupper() for char in snippet]):
            filtered_predictions[span] = entity_prediction
    return filtered_predictions


class AbstractPredictionReader:
    """
    To write a custom PredictionReader, inherit from AbstractPredictionReader
    and implement one of the two methods predictions_iterator() and
    get_predictions_with_text_from_file().

    Implement predictions_iterator() if you are sure that the order in which
    the predictions are read corresponds to the article order in the benchmark.
    Set predictions_iterator_implemented = True when calling super().__init__()

    Implement get_predictions_with_text_from_file() if you are not sure that
    the order in which the predictions are read corresponds to the article
    order in the benchmark and the prediction file contains the original
    article texts.
    Set predictions_iterator_implemented = False when calling super().__init__()
    """
    def __init__(self, input_filepath: str, predictions_iterator_implemented: bool):
        self.input_filepath = input_filepath
        self.predictions_iterator_implemented = predictions_iterator_implemented
        self.linker_identifier = "Unknown Linker"

        # Needed only if predictions_iterator_implemented is True
        # Iterator over the predictions for each article
        self.iterator: Iterator[Dict[Tuple[int, int], EntityPrediction]]

        # Needed only if predictions_iterator_implemented is False
        self.compare_length = 100
        # Dictionary that maps the first <compare_length> characters of an article text to the index of the article
        self.article_texts2prediction_index: Dict[str, int] = {}
        # List of predictions where the predictions for article with index i are the ith entry in the list
        self.predictions: List[Dict[Tuple[int, int], EntityPrediction]] = []
        # List of predictions where the predictions for article with index i are the ith entry in the list
        self.prediction_article_texts: List[str] = []

        if predictions_iterator_implemented:
            self.iterator = self.predictions_iterator()
        else:
            self.build_prediction_mappings(self.input_filepath)

    def set_linker_identifier(self, linker_identifier: str):
        self.linker_identifier = linker_identifier

    def predictions_iterator(self) -> Iterator[Dict[Tuple[int, int], EntityPrediction]]:
        """
        Yields predictions for each article.

        Implement this method if you are sure that the order in which the
        predictions are read corresponds to the article order in the benchmark.

        :return: iterator over dictionaries with predictions for each article
        """
        raise NotImplementedError()

    def get_predictions_with_text_from_file(self, filepath) -> Iterator[Tuple[Dict[Tuple[int, int], EntityPrediction],
                                                                              str]]:
        """
        Yields predictions and article text for each article in the file

        Implement this method if you are not sure that the order in which the
        predictions are read corresponds to the article order in the benchmark
        and the prediction file contains the original article texts.

        :return: iterator over dictionaries with predictions for each article and the article text
        """
        raise NotImplementedError()

    def build_prediction_mappings(self, input_filepath):
        """
        Build the following mappings:
        - self.article_texts2prediction_index: Dict[str, int]
          maps the first <self.compare_length> characters of a prediction article text to an article index
        - self.predictions: List[Dict[Tuple[int, int], EntityPrediction]]
          a list of predictions where the prediction for article with index i is the ith list entry
        - self.prediction_article_texts: List[str]
          a list of article texts where the article text for article with index i is the ith list entry
        """
        if os.path.isdir(input_filepath):
            for filename in sorted(os.listdir(input_filepath)):
                filepath = os.path.join(input_filepath, filename)
                for predictions, text in self.get_predictions_with_text_from_file(filepath):
                    self.article_texts2prediction_index[text[:self.compare_length]] = len(self.predictions)
                    self.predictions.append(predictions)
                    self.prediction_article_texts.append(text)
        else:
            for predictions, text in self.get_predictions_with_text_from_file(input_filepath):
                self.article_texts2prediction_index[text[:self.compare_length]] = len(self.predictions)
                self.predictions.append(predictions)
                self.prediction_article_texts.append(text)

    def get_predictions_by_article(self, article: Article) -> Dict[Tuple[int, int], EntityPrediction]:
        """
        Returns the predictions whose article text matches the text of the given article.

        :return: dictionary with predictions for the article
        """
        if article.text[:self.compare_length] in self.article_texts2prediction_index:
            index = self.article_texts2prediction_index[article.text[:self.compare_length]]
            prediction_article_text = self.prediction_article_texts[index]
            if prediction_article_text != article.text:
                logger.warning("Benchmark article text and prediction article text are similar,"
                               "but not completely the same. len(benchmark_article) = %d, len(prediction_article) = %d"
                               % (len(article.text), len(prediction_article_text)))
            return self.predictions[index]
        else:
            logger.warning("No corresponding prediction article found for benchmark article \"%s...\""
                           "Returning empty predictions." % article.text[:self.compare_length])
            return {}

    def get_predictions(self, article: Article) -> Dict[Tuple[int, int], EntityPrediction]:
        """
        Returns the predictions for the given article.

        If a prediction iterator was implemented, this simply returns the next predictions in the iterator.
        Otherwise returns the predictions whose article text matches the text of the given article.

        :return: dictionary with predictions for the article
        """
        if self.predictions_iterator_implemented:
            return next(self.iterator)
        else:
            return self.get_predictions_by_article(article)

    def link_entities(self, article: Article, uppercase: Optional[bool] = False):
        """
        Link the entities in the article as retrieved with the prediction reader.
        """
        predictions = self.get_predictions(article)
        if uppercase:
            predictions = uppercase_predictions(predictions, article.text)
        article.link_entities(predictions, self.linker_identifier, self.linker_identifier)
