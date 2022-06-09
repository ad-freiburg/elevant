import logging
from typing import Dict, Tuple, Optional, Any

import tagme

from src.models.entity_database import EntityDatabase
from src.models.entity_prediction import EntityPrediction
from src.linkers.abstract_entity_linker import AbstractEntityLinker
from src.utils.knowledge_base_mapper import KnowledgeBaseMapper

logger = logging.getLogger("main." + __name__.split(".")[-1])

tagme.GCUBE_TOKEN = "56af583d-5f6e-496f-aea2-eab06673b6a3-843339462"


class TagMeLinker(AbstractEntityLinker):
    def __init__(self, entity_db: EntityDatabase, config: Dict[str, Any]):
        self.entity_db = entity_db
        self.model = None

        # Get config variables
        self.linker_identifier = config["name"] if "name" in config else "TagMe"
        self.ner_identifier = self.linker_identifier
        self.rho_threshold = config["rho_threshold"] if "rho_threshold" in config else 0.2

    def predict(self,
                text: str,
                doc=None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
        annotations = tagme.annotate(text).get_annotations(self.rho_threshold)
        annotations = sorted(annotations, key=lambda a: a.score, reverse=True)
        predictions = {}
        count = 0
        for ann in annotations:
            entity_id = KnowledgeBaseMapper.get_wikidata_qid(ann.entity_title, self.entity_db)
            if entity_id is None:
                logger.warning("\nNo mapping to Wikidata found for label '%s'" % ann.entity_title)
                count += 1
            span = (ann.begin, ann.end)
            snippet = text[span[0]:span[1]]
            if uppercase and snippet.islower():
                continue
            predictions[span] = EntityPrediction(span, entity_id, {entity_id})

        if count > 0:
            logger.warning("\n%d entity labels could not be matched to any Wikidata id." % count)
        return predictions

    def has_entity(self, entity_id: str) -> bool:
        return True
