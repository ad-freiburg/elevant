import logging
from typing import Dict, Tuple, Optional, Any

from elevant.models.entity_prediction import EntityPrediction
from elevant.linkers.abstract_entity_linker import AbstractEntityLinker
from refined.inference.processor import Refined

from elevant.utils.knowledge_base_mapper import UnknownEntity

logger = logging.getLogger("main." + __name__.split(".")[-1])


class RefinedLinker(AbstractEntityLinker):
    def __init__(self, config: Dict[str, Any]):
        self.model = None

        # Get config variables
        self.linker_identifier = config["linker_name"] if "linker_name" in config else "Refined"
        self.ner_identifier = self.linker_identifier
        model_name = config["model_name"] if "model_name" in config else "aida_model"
        entity_set = config["entity_set"] if "entity_set" in config else "wikipedia"

        self.refined = Refined.from_pretrained(model_name=model_name, entity_set=entity_set)

    def predict(self,
                text: str,
                doc=None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
        annotations = self.refined.process_text(text)
        predictions = {}
        for ann in annotations:
            entity_id = ann.predicted_entity.wikidata_entity_id
            span = (ann.start, ann.start + ann.ln)
            snippet = text[span[0]:span[1]]
            if uppercase and snippet.islower():
                continue
            candidates = {c for c, score in ann.candidate_entities}
            if entity_id is None:
                entity_id = UnknownEntity.NIL.value
            predictions[span] = EntityPrediction(span, entity_id, candidates)
        return predictions

    def has_entity(self, entity_id: str) -> bool:
        return True
