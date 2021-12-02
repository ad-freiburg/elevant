import logging

from typing import Dict, Tuple, Iterator

from src.models.entity_prediction import EntityPrediction

logger = logging.getLogger("main." + __name__.split(".")[-1])


class BertPredictionReader:
    @staticmethod
    def article_predictions_iterator(disambiguation_file: str) -> Iterator[Dict[Tuple[int, int], EntityPrediction]]:
        """
        Yields all non-None BERT entity predictions in the given file.

        :param disambiguation_file: path to file with the BERT disambiguation results
        :return: iterator over predictions for each linked article
        """
        with open(disambiguation_file, "r") as file:
            article_predictions = {}
            last_article_id = -1
            for line in file:
                article_id, start_span, end_span, entity_id = line.strip().split("\t")
                article_id = int(article_id)
                span = (int(start_span), int(end_span) + 1)
                if last_article_id != -1 and last_article_id != article_id:
                    yield article_predictions
                    article_predictions = {}
                while last_article_id != -1 and last_article_id < article_id - 1:
                    # Article does not contain any mentions
                    last_article_id += 1
                    yield {}
                if entity_id != "None":
                    article_predictions[span] = EntityPrediction(span, entity_id, {entity_id})
                last_article_id = article_id
        yield article_predictions
