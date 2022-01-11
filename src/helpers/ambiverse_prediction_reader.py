from typing import Dict, Tuple, Iterator
import os
import json
import logging

from src.models.entity_prediction import EntityPrediction

logger = logging.getLogger("main." + __name__.split(".")[-1])


class AmbiversePredictionReader:
    def __init__(self, entity_db):
        self.entity_db = entity_db

    def _get_prediction_from_file(self, file_path: str) -> Dict[Tuple[int, int], EntityPrediction]:
        """
        Yields all predictions in the given ambiverse disambiguation result file

        :param file_path: path to the ambiverse result file
        :return: dictionary that contains all predictions for the given file
        """
        result = json.load(open(file_path))
        predictions = {}
        for match in result["matches"]:
            span_start = match["charOffset"]
            span_end = span_start + match["charLength"]
            span = (span_start, span_end)
            entity_id = match["entity"]["id"].split("/")[-1] if match["entity"] else None
            if entity_id not in predictions:
                predictions[entity_id] = []
            predictions[entity_id].append(span)

        new_predictions = {}
        if "entities" in result:
            for entity in result["entities"]:
                entity_id = entity["id"].split("/")[-1]
                if entity_id == "null":
                    continue
                matching_predictions_spans = predictions[entity_id]
                name = entity["name"]
                entity_id_from_link = self.entity_db.link2id(name)
                if entity_id_from_link and entity_id != entity_id_from_link:
                    logger.debug("Result QID does not match QID retrieved via result Wikipedia URL: %s vs %s" %
                                 (entity_id, entity_id_from_link))
                    entity_id = entity_id_from_link
                for span in matching_predictions_spans:
                    new_predictions[span] = EntityPrediction(span, entity_id, {entity_id})
        else:
            logger.info("matches exists, but entities does not. Previous predictions: " % predictions)
        return new_predictions

    def article_predictions_iterator(self, disambiguation_dir: str) -> Iterator[Dict[Tuple[int, int], EntityPrediction]]:
        """
        Yields predictions for each ambiverse disambiguation result file in the given directory

        :param disambiguation_dir: path to the directory that contains the ambiverse disambiguation results
        :return: iterator over predictions for each file in the given directory
        """
        for file in sorted(os.listdir(disambiguation_dir)):
            file_path = os.path.join(disambiguation_dir, file)
            predictions = self._get_prediction_from_file(file_path)
            yield predictions
