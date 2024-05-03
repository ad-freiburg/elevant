from typing import Dict, Tuple, Iterator, List
import json
import logging

from elevant.models.entity_prediction import EntityPrediction
from elevant.prediction_readers.abstract_prediction_reader import AbstractPredictionReader

logger = logging.getLogger("main." + __name__.split(".")[-1])


class EPGELPredictionReader(AbstractPredictionReader):
    def __init__(self, input_filepath: str):
        super().__init__(input_filepath, predictions_iterator_implemented=True)

    def _get_prediction_from_files(self, input_file_path: str) -> List[Dict[Tuple[int, int], EntityPrediction]]:
        """
        Yields all predictions in the disambiguation_file.

        :param input_file_path: path to the EPGEL input file
        :return: dictionary that contains all predictions for the given file
        """
        # We cannot change the output, but we can add information to the input, e.g. the span of the mention
        # and the article index within the benchmark.
        input_lines = open(input_file_path).readlines()
        output_lines = open(self.input_filepath).readlines()

        last_article_idx = json.loads(input_lines[-1])["article_index"]
        all_article_predictions = [{} for _ in range(last_article_idx + 1)]

        if len(input_lines) != len(output_lines):
            logger.error("Number of input mentions and output predictions differ: %d vs %d"
                         % (len(input_lines), len(output_lines)))
        else:
            for i in range(len(input_lines)):
                input_json = json.loads(input_lines[i])
                output_json = json.loads(output_lines[i])
                article_idx = input_json["article_index"]
                span = input_json["mention_start"], input_json["mention_end"]
                entity_id = None
                candidates = set()
                if len(output_json["candidates"]) > 0:
                    entity_id = output_json["candidates"][0]
                    candidates = set(output_json["candidates"])
                all_article_predictions[article_idx][span] = EntityPrediction(span, entity_id, candidates)

        return all_article_predictions

    def predictions_iterator(self) -> Iterator[Dict[Tuple[int, int], EntityPrediction]]:
        """
        Yields predictions for the disambiguation_file.

        :return: iterator over dictionaries with predictions for each article
        """
        input_file_path = self.input_filepath.replace("output", "input")
        all_article_predictions = self._get_prediction_from_files(input_file_path)
        for predictions in all_article_predictions:
            yield predictions
