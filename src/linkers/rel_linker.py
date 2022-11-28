import logging
from typing import Dict, Tuple, Optional, Any

import requests
import json

from src.models.entity_database import EntityDatabase
from src.models.entity_prediction import EntityPrediction
from src.linkers.abstract_entity_linker import AbstractEntityLinker
from src.utils.knowledge_base_mapper import KnowledgeBaseMapper


logger = logging.getLogger("main." + __name__.split(".")[-1])


class RelLinker(AbstractEntityLinker):
    def __init__(self, entity_db: EntityDatabase, config: Dict[str, Any]):
        self.entity_db = entity_db
        self.model = None

        # Get config variables
        self.linker_identifier = config["linker_name"] if "linker_name" in config else "REL"
        self.ner_identifier = self.linker_identifier
        self.url = config["api_url"] if "api_url" in config else "https://rel.cs.ru.nl/api"

    def predict(self,
                text: str,
                doc=None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
        annotations = requests.post(self.url, json={"text": text, "spans": []}).json()
        predictions = {}
        for ann in annotations:
            entity_name = ann[3]
            entity_id = KnowledgeBaseMapper.get_wikidata_qid(entity_name, self.entity_db)
            span = (ann[0], ann[0] + ann[1])
            snippet = text[span[0]:span[1]]
            if uppercase and snippet.islower():
                continue
            predictions[span] = EntityPrediction(span, entity_id, {entity_id})
        return predictions

    def has_entity(self, entity_id: str) -> bool:
        return True
