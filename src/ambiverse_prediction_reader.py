import os
import json

from src.entity_mention import EntityMention
from src.entity_prediction import EntityPrediction


class AmbiversePredictionReader:
    LINKER_IDENTIFIER = "AMBIVERSE"
    NER_IDENTIFIER = "AMBIVERSE"

    @classmethod
    def _get_prediction_from_file(cls, file_path):
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
            candidates = {entity_id}
            entity_mention = EntityMention(span,
                                           recognized_by=cls.NER_IDENTIFIER,
                                           entity_id=entity_id,
                                           linked_by=cls.LINKER_IDENTIFIER)
            predictions[span] = entity_mention, candidates
        return predictions

    @staticmethod
    def article_predictions_iterator(disambiguation_dir):
        """
        Yields predictions for each ambiverse disambiguation result file in the given directory

        :param disambiguation_dir: path to the directory that contains the ambiverse disambiguation results
        :return: iterator over predictions for each file in the given directory
        """
        for file in sorted(os.listdir(disambiguation_dir)):
            file_path = os.path.join(disambiguation_dir, file)
            predictions = AmbiversePredictionReader._get_prediction_from_file(file_path)
            yield predictions
