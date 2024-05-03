import logging
from typing import Dict, Tuple, Optional, Any

import tagme

from elevant.models.entity_database import EntityDatabase
from elevant.models.entity_prediction import EntityPrediction
from elevant.linkers.abstract_entity_linker import AbstractEntityLinker
from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper

logger = logging.getLogger("main." + __name__.split(".")[-1])


class TagMeLinker(AbstractEntityLinker):
    def __init__(self, entity_db: EntityDatabase, config: Dict[str, Any]):
        self.entity_db = entity_db
        self.model = None

        # Get config variables
        self.linker_identifier = config["linker_name"] if "linker_name" in config else "TagMe"
        self.ner_identifier = self.linker_identifier
        self.rho_threshold = config["rho_threshold"] if "rho_threshold" in config else 0.2
        if "token" not in config or config["token"] in ("", "replace with your own access token"):
            logger.error("You need an access token in order to run the TagMe Linker.\nSee "
                         "https://github.com/marcocor/tagme-python for instructions on how to get the token. "
                         "(It's easy!)\nThen set your personal access token in configs/tagme.config.json .")
            raise RuntimeError('No valid TagMe access token provided.')
        else:
            tagme.GCUBE_TOKEN = config["token"]

    def predict(self,
                text: str,
                doc=None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
        annotations = tagme.annotate(text).get_annotations(self.rho_threshold)
        annotations = sorted(annotations, key=lambda a: a.score, reverse=True)
        predictions = {}
        for ann in annotations:
            entity_id = KnowledgeBaseMapper.get_wikidata_qid(ann.entity_title, self.entity_db)
            span = (ann.begin, ann.end)
            snippet = text[span[0]:span[1]]
            if uppercase and snippet.islower():
                continue
            predictions[span] = EntityPrediction(span, entity_id, {entity_id})

        return predictions

    def has_entity(self, entity_id: str) -> bool:
        return True
