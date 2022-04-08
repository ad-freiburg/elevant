from typing import Iterator, Tuple, Dict

from src.models.entity_database import EntityDatabase
from src.models.entity_prediction import EntityPrediction

import json
import logging

from src.utils.knowledge_base_mapper import KnowledgeBaseMapper
from src.prediction_readers.abstract_prediction_reader import AbstractPredictionReader

logger = logging.getLogger("main." + __name__.split(".")[-1])


class SimpleJsonlPredictionReader(AbstractPredictionReader):
    def __init__(self, input_filepath: str, entity_db: EntityDatabase):
        self.entity_db = entity_db
        super().__init__(input_filepath, predictions_iterator_implemented=True)

    def _get_prediction_from_jsonl(self, string: str) -> Dict[Tuple[int, int], EntityPrediction]:
        """
        Extract entity predictions from a string that is the output of the
        Neural EL system by Gupta et al.
        """
        link_json = json.loads(string)
        links = link_json["predictions"]
        predictions = {}
        for link in links:
            entity_reference = link["entity_reference"]
            # If the entity reference is not a URI and is not from Wikidata, references in the format "Q[0-9]+"
            # will be wrongly assumed to be Wikidata QIDs
            entity_id = KnowledgeBaseMapper.get_wikidata_qid(entity_reference, self.entity_db, verbose=False)
            start = link["start_char"]
            end = link["end_char"]
            span = (start, end)
            candidates = {entity_id}  # The Simple JSON Format does not provide information about candidates
            predictions[span] = EntityPrediction(span, entity_id, candidates)
        return predictions

    def predictions_iterator(self) -> Iterator[Dict[Tuple[int, int], EntityPrediction]]:
        """
        Yields predictions for each Neural EL disambiguation result in the
        disambiguation_file with one line per article.

        :return: iterator over dictionaries with predictions for each article
        """
        with open(self.input_filepath, "r", encoding="utf8") as file:
            for line in file:
                predictions = self._get_prediction_from_jsonl(line)
                yield predictions
