import logging
from typing import Dict, Tuple, Optional, Any

from src.models.entity_database import EntityDatabase
from src.models.entity_prediction import EntityPrediction
from src.linkers.abstract_entity_linker import AbstractEntityLinker
from src.utils.knowledge_base_mapper import KnowledgeBaseMapper
from refined.inference.processor import Refined


logger = logging.getLogger("main." + __name__.split(".")[-1])


class RefinedLinker(AbstractEntityLinker):
    def __init__(self, entity_db: EntityDatabase, config: Dict[str, Any]):
        self.entity_db = entity_db
        self.model = None

        # Get config variables
        self.linker_identifier = config["linker_name"] if "linker_name" in config else "Refined"
        self.ner_identifier = self.linker_identifier
        model_name = config["model_name"] if "model_name" in config else "wikipedia_model"
        entity_set = config["entity_set"] if "entity_set" in config else "wikipedia"

        self.refined = Refined.from_pretrained(model_name=model_name, entity_set=entity_set)

    def predict(self,
                text: str,
                doc=None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
        annotations = self.refined.process_text(text)
        predictions = {}
        for ann in annotations:
            entity_id = self.get_entity_id(ann.predicted_entity)
            span = (ann.start, ann.start + ann.ln)
            snippet = text[span[0]:span[1]]
            if uppercase and snippet.islower():
                continue
            candidates = {c for c, score in ann.candidate_entities}
            predictions[span] = EntityPrediction(span, entity_id, candidates)
        return predictions

    def get_entity_id(self, predicted_entity):
        if predicted_entity.wikidata_entity_id:
            return predicted_entity.wikidata_entity_id
        else:
            entity_name = predicted_entity.wikipedia_entity_title
            return KnowledgeBaseMapper.get_wikidata_qid(entity_name, self.entity_db)

    def has_entity(self, entity_id: str) -> bool:
        return True
