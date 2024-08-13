import logging
import requests
from typing import Dict, Tuple, Optional
from pynif import NIFCollection

from elevant.models.entity_database import EntityDatabase
from elevant.models.entity_prediction import EntityPrediction
from elevant.linkers.abstract_entity_linker import AbstractEntityLinker
from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper, UnknownEntity

logger = logging.getLogger("main." + __name__.split(".")[-1])


def create_nif(text, context_num):
    collection_uri = "http://example.org/"
    collection = NIFCollection(uri=collection_uri)
    context = collection.add_context(uri=collection_uri + str(context_num), mention=text)
    return context.turtle


class NifApiLinker(AbstractEntityLinker):
    def __init__(self, entity_db: EntityDatabase, url: str, linker_name: str, custom_kb: Optional[bool] = False):
        self.entity_db = entity_db
        self.model = None

        self.linker_identifier = linker_name
        self.ner_identifier = self.linker_identifier
        self.api_url = url
        self.custom_kb = custom_kb

        self.context_num = 0

    def predict(self,
                text: str,
                doc=None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:

        nif_article = create_nif(text, self.context_num)
        self.context_num += 1

        # Send the POST request
        response = requests.post(self.api_url, data=nif_article.encode("utf-8"))

        # Get the response from the server
        nif_prediction = response.text
        print(nif_prediction)

        predictions = {}
        nif_doc = NIFCollection.loads(nif_prediction)
        # NIF contexts have random order by default. Make sure results are reproducible by sorting by URI
        for context in sorted(nif_doc.contexts, key=lambda c: c.uri):
            text = context.mention
            if not text:
                # This happens e.g. in KORE50 for the parent context
                # <http://www.mpi-inf.mpg.de/yago-naga/aida/download/KORE50.tar.gz/AIDA.tsv>
                continue
            predictions = {}
            # Make sure predictions are sorted by start index
            for phrase in sorted(context.phrases, key=lambda p: p.beginIndex):
                entity_uri = phrase.taIdentRef
                if self.custom_kb:
                    entity_id = entity_uri if entity_uri else UnknownEntity.NIL.value
                else:
                    entity_id = KnowledgeBaseMapper.get_wikidata_qid(entity_uri, self.entity_db, verbose=True)
                span = phrase.beginIndex, phrase.endIndex
                predictions[span] = EntityPrediction(span, entity_id, {entity_id})
        return predictions

    def has_entity(self, entity_id: str) -> bool:
        return True
