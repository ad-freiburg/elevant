from typing import Iterator, Tuple, Dict, Optional

from elevant.models.entity_database import EntityDatabase
from elevant.models.entity_prediction import EntityPrediction

import json
import logging

from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper, UnknownEntity
from elevant.prediction_readers.abstract_prediction_reader import AbstractPredictionReader

logger = logging.getLogger("main." + __name__.split(".")[-1])


class SimpleJsonlPredictionReader(AbstractPredictionReader):
    def __init__(self, input_filepath: str, entity_db: EntityDatabase, custom_kb: Optional[bool] = False):
        self.entity_db = entity_db
        self.custom_kb = custom_kb
        super().__init__(input_filepath, predictions_iterator_implemented=True)

    def _get_prediction_from_jsonl(self, string: str) -> Dict[Tuple[int, int], EntityPrediction]:
        """
        Extract entity predictions from a string that is in simple JSONL format.
        E.g. the output of the Neural EL system by Gupta et al.
        """
        link_json = json.loads(string)
        raw_predictions = link_json["predictions"]
        predictions = {}
        for raw_prediction in raw_predictions:
            entity_reference = raw_prediction["entity_reference"]
            # If the entity reference is not a URI and is not from Wikidata, references in the format "Q[0-9]+"
            # will be wrongly assumed to be Wikidata QIDs
            if self.custom_kb:
                entity_id = entity_reference if entity_reference else UnknownEntity.NIL.value
            else:
                entity_id = KnowledgeBaseMapper.get_wikidata_qid(entity_reference, self.entity_db, verbose=False)
            span = raw_prediction["start_char"], raw_prediction["end_char"]
            candidates = {entity_id}
            if "candidates" in raw_prediction:
                for cand in raw_prediction["candidates"]:
                    cand_id = KnowledgeBaseMapper.get_wikidata_qid(cand, self.entity_db, verbose=False)
                    # Do not add unknown entities to the candidates
                    if not KnowledgeBaseMapper.is_unknown_entity(cand_id):
                        candidates.add(cand_id)
            predictions[span] = EntityPrediction(span, entity_id, candidates)
        return predictions

    def predictions_iterator(self) -> Iterator[Dict[Tuple[int, int], EntityPrediction]]:
        """
        Yields predictions for each disambiguation result in the disambiguation
        file with one line per article.

        :return: iterator over dictionaries with predictions for each article
        """
        with open(self.input_filepath, "r", encoding="utf8") as file:
            for line in file:
                predictions = self._get_prediction_from_jsonl(line)
                yield predictions
