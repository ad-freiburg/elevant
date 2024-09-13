import logging
from typing import Dict, Tuple, Optional, Any

import requests

from elevant.models.entity_database import EntityDatabase
from elevant.models.entity_prediction import EntityPrediction
from elevant.linkers.abstract_entity_linker import AbstractEntityLinker
from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper

logger = logging.getLogger("main." + __name__.split(".")[-1])


class WatLinker(AbstractEntityLinker):
    def __init__(self, entity_db: EntityDatabase, config: Dict[str, Any]):
        self.entity_db = entity_db
        self.model = None

        # Get config variables
        self.linker_identifier = config["linker_name"] if "linker_name" in config else "WAT"
        self.ner_identifier = self.linker_identifier
        self.api_url = config["api_url"] if "api_url" in config else "https://wat.d4science.org/wat/tag/tag"
        self.rho_threshold = config["rho_threshold"] if "rho_threshold" in config else None
        if "token" not in config or config["token"] in ("", "replace with your own access token"):
            logger.error("You need an access token in order to run the WAT Linker.\nSee "
                         "https://github.com/marcocor/tagme-python for instructions on how to get the token. "
                         "(It's easy!)\nThen set your personal access token in configs/wat.config.json .")
            raise RuntimeError('No valid WAT access token provided.')
        else:
            self.GCUBE_TOKEN = config["token"]

    def predict(self,
                text: str,
                doc=None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:

        # Main method, text annotation with WAT entity linking system
        payload = [("gcube-token", self.GCUBE_TOKEN),
                   ("text", text),
                   ("lang", 'en')]

        response = requests.get(self.api_url, params=payload)
        annotations = [WatAnnotation(a) for a in response.json()['annotations']]

        predictions = {}
        for ann in annotations:
            if not self.rho_threshold or ann.rho >= self.rho_threshold:
                entity_id = KnowledgeBaseMapper.get_wikidata_qid(ann.wiki_title, self.entity_db)
                span = (ann.start, ann.end)
                snippet = text[span[0]:span[1]]
                if uppercase and snippet.islower():
                    continue

                predictions[span] = EntityPrediction(span, entity_id, {entity_id})

        return predictions

    def has_entity(self, entity_id: str) -> bool:
        return True


class WatAnnotation:
    """
    An entity annotated by WAT. Taken from https://sobigdata.d4science.org/web/tagme/wat-api
    """

    def __init__(self, d):
        # char offset (included)
        self.start = d['start']
        # char offset (not included)
        self.end = d['end']
        # annotation accuracy
        self.rho = d['rho']
        # Wikpedia entity info
        self.wiki_id = d['id']
        self.wiki_title = d['title']
