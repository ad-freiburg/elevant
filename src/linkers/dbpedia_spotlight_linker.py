from typing import Optional, Dict, Tuple

import requests
import logging

from pynif import NIFCollection
from spacy.tokens.doc import Doc

from src.linkers.abstract_entity_linker import AbstractEntityLinker
from src.models.entity_prediction import EntityPrediction
from src.models.entity_database import EntityDatabase
from src.utils.knowledge_base_mapper import KnowledgeBaseMapper

logger = logging.getLogger("main." + __name__.split(".")[-1])


class DbpediaSpotlightLinker(AbstractEntityLinker):
    """
    In order to use this linker, the DBpedia Spotlight API must be running at
    http://localhost:<specified_port>
    For instructions on starting the API using Docker see
    https://hub.docker.com/r/dbpedia/dbpedia-spotlight

    Alternatively, change the API URL to the official API at
    https://api.dbpedia-spotlight.org/en/annotate
    """
    NER_IDENTIFIER = "DBPEDIA_SPOTLIGHT"
    LINKER_IDENTIFIER = "DBPEDIA_SPOTLIGHT"

    def __init__(self, entity_db: EntityDatabase, port: int, confidence: Optional[float] = 0.35):
        self.entity_db = entity_db
        self.port = port  # DBPedia server needs to be running on the local machine at the specified port
        self.confidence = confidence
        self.model = None

    def predict(self, text: str,
                doc: Optional[Doc] = None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
        data = {"text": text, "confidence": self.confidence}
        r = requests.post("http://localhost:" + str(self.port) + "/rest/annotate",
                          data=data,
                          headers={'Accept': 'text/turtle'})
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
