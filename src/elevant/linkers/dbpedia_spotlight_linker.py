from typing import Optional, Dict, Tuple, Any

import requests
import logging

from pynif import NIFCollection
from spacy.tokens.doc import Doc

from elevant.linkers.abstract_entity_linker import AbstractEntityLinker
from elevant.models.entity_prediction import EntityPrediction
from elevant.models.entity_database import EntityDatabase
from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper

logger = logging.getLogger("main." + __name__.split(".")[-1])


class DbpediaSpotlightLinker(AbstractEntityLinker):
    """
    Instead of using the official DBpedia Spotlight API (default) you can also
    run your own instance of DBpedia Spotlight and adjust the api_url in the
    DBpedia Spotlight config at configs/dbpedia-spotlight.config.json accordingly.
    For instructions on starting your own API using Docker see
    https://hub.docker.com/r/dbpedia/dbpedia-spotlight
    """
    def __init__(self, entity_db: EntityDatabase, config: Dict[str, Any]):
        self.entity_db = entity_db
        self.model = None

        # Get config variables
        self.linker_identifier = config["linker_name"] if "linker_name" in config else "DBpedia Spotlight"
        self.ner_identifier = self.linker_identifier
        self.api_url = config["api_url"] if "api_url" in config else "https://api.dbpedia-spotlight.org/en/annotate"
        self.confidence = config["confidence"] if "confidence" in config else None
        self.types = config["types"] if "types" in config else None
        self.support = config["support"] if "support" in config else None

    def predict(self, text: str,
                doc: Optional[Doc] = None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
        data = {"text": text}
        if self.confidence:
            data["confidence"] = self.confidence
        if self.support:
            data["support"] = self.support
        if self.types:
            data["types"] = ",".join(self.types)

        r = requests.post(self.api_url, data=data, headers={'Accept': 'text/turtle'})
        result = r.content

        nif_doc = NIFCollection.loads(result)
        predictions = {}
        for context in nif_doc.contexts:  # There should be just one context for a single benchmark article
            for phrase in context.phrases:
                entity_uri = phrase.taIdentRef
                entity_id = KnowledgeBaseMapper.get_wikidata_qid(entity_uri, self.entity_db, verbose=True)
                span = phrase.beginIndex, phrase.endIndex
                snippet = text[span[0]:span[1]]
                if uppercase and snippet.islower():
                    continue
                predictions[span] = EntityPrediction(span, entity_id, {entity_id})
        return predictions

    def has_entity(self, entity_id: str) -> bool:
        return True
