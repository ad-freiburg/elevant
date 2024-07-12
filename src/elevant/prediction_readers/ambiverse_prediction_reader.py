from typing import Dict, Tuple, Iterator
import os
import json
import logging

from elevant.models.entity_database import EntityDatabase
from elevant.models.entity_prediction import EntityPrediction
from elevant.prediction_readers.abstract_prediction_reader import AbstractPredictionReader
from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper, UnknownEntity

logger = logging.getLogger("main." + __name__.split(".")[-1])


class AmbiversePredictionReader(AbstractPredictionReader):
    def __init__(self, input_filepath: str, entity_db: EntityDatabase):
        self.entity_db = entity_db
        super().__init__(input_filepath, predictions_iterator_implemented=True)

    def _get_prediction_from_file(self, file_path: str) -> Dict[Tuple[int, int], EntityPrediction]:
        """
        Yields all predictions in the given ambiverse disambiguation result file

        :param file_path: path to the ambiverse result file
        :return: dictionary that contains all predictions for the given file
        """
        result = json.load(open(file_path))

        ambiverse_entity_id_mapping = {}
        if "entities" in result:
            # Ambiverse predicted QIDs can contain mistakes, therefore use custom rules to map entities to Wikidata QIDs
            # instead of using KnowledgeBaseMapping.get_wikidata_qid()
            for entity in result["entities"]:
                entity_id = entity["id"].split("/")[-1]
                if entity_id != "null":
                    # QIDs predicted by Ambiverse often do not match the predicted entity name.
                    # The entity name is more trustworthy.
                    entity_id_from_name = KnowledgeBaseMapper.get_wikidata_qid(entity["name"], self.entity_db,
                                                                               verbose=False)
                    if not KnowledgeBaseMapper.is_unknown_entity(entity_id_from_name):
                        ambiverse_entity_id_mapping[entity_id] = entity_id_from_name

        predictions = {}
        for match in result["matches"]:
            span_start = match["charOffset"]
            span_end = span_start + match["charLength"]
            span = (span_start, span_end)
            entity_id = match["entity"]["id"].split("/")[-1] if match["entity"] else UnknownEntity.NIL.value
            entity_id = entity_id if entity_id else UnknownEntity.NIL.value  # Change empty string to NIL
            if entity_id in ambiverse_entity_id_mapping and ambiverse_entity_id_mapping[entity_id]:
                if entity_id != ambiverse_entity_id_mapping[entity_id]:
                    logger.debug("Result QID does not match QID retrieved via result Wikipedia URL: %s vs %s" %
                                 (entity_id, ambiverse_entity_id_mapping[entity_id]))
                entity_id = ambiverse_entity_id_mapping[entity_id]
            predictions[span] = EntityPrediction(span, entity_id, {entity_id})

        return predictions

    def predictions_iterator(self) -> Iterator[Dict[Tuple[int, int], EntityPrediction]]:
        """
        Yields predictions for each ambiverse disambiguation result file in the disambiguation_dir.

        :return: iterator over dictionaries with predictions for each article
        """
        for file in sorted(os.listdir(self.input_filepath)):
            file_path = os.path.join(self.input_filepath, file)
            predictions = self._get_prediction_from_file(file_path)
            yield predictions
