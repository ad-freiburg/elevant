from enum import Enum
from typing import Optional
from urllib.parse import unquote

import re
import logging

from src.models.entity_database import EntityDatabase

logger = logging.getLogger("main." + __name__.split(".")[-1])


class KnowledgeBaseName(Enum):
    WIKIDATA = "wikidata"
    WIKIPEDIA = "wikipedia"
    DBPEDIA = "dbpedia"


class KnowledgeBase:
    def __init__(self, name: KnowledgeBaseName, entity_uri_prefix: str):
        self.name = name
        self.entity_uri_prefix = entity_uri_prefix


class KnowledgeBaseMapper:
    wikidata_kb = KnowledgeBase(KnowledgeBaseName.WIKIDATA, "www.wikidata.org/wiki/")
    wikipedia_kb = KnowledgeBase(KnowledgeBaseName.WIKIPEDIA, "en.wikipedia.org/wiki/")
    dbpedia_kb = KnowledgeBase(KnowledgeBaseName.DBPEDIA, "dbpedia.org/resource/")
    kbs = [wikidata_kb, wikipedia_kb, dbpedia_kb]

    @staticmethod
    def identify_kb(entity_uri: str) -> Optional[KnowledgeBaseName]:
        """ Identify the knowledge base in which an entity was referenced from
        the given entity URI.
        """
        for kb in KnowledgeBaseMapper.kbs:
            # Don't use startswith because it could start with http or https
            if kb.entity_uri_prefix in entity_uri:
                return kb.name
        return None

    @staticmethod
    def get_wikidata_qid(entity_reference: str, entity_db: EntityDatabase, verbose: Optional[bool] = False)\
            -> Optional[str]:
        """ Given a reference string to an entity and an EntityDatabase with
        the Wikipedia to Wikidata mapping loaded, try to retrieve the Wikidata
        QID of the referenced entity.
        Returns None if the entity can't be mapped to a Wikidata QID
        """
        # The last part of a URI is the entity name / identifier.
        # This still works if the entity_reference is not a URI and does not contain a "/" (result of rfind is -1)
        entity_name = entity_reference[entity_reference.rfind("/") + 1:]

        if not entity_name:
            logger.info("Empty entity name. Probably a NIL prediction.")
            return None

        # Try to identify the used KB
        kb_name = KnowledgeBaseMapper.identify_kb(entity_reference)
        if not kb_name and verbose:
            logger.info("Unknown knowledge base in entity URI: %s. Trying to infer KB from entity name."
                        % entity_reference)

        # Retrieve Wikidata QID based on identified KB or entity name
        if kb_name == KnowledgeBaseName.WIKIDATA or (not kb_name and re.match(r"Q[0-9]+", entity_name)):
            entity_id = entity_name
        elif entity_name:
            if entity_name != entity_reference:
                # Unquote entity name only if it was part of a URI
                entity_name = unquote(entity_name)
            entity_name = entity_name.replace('_', ' ')
            # This should work for both Wikipedia and DBpedia entity names
            entity_id = entity_db.link2id(entity_name)
            if not entity_id:
                logger.warning("Entity name %s could not be mapped to a Wikidata QID." % entity_name)
                return None
        else:
            # The entity ID is None if the provided entity ID is not a QID or cannot be mapped from
            # Wikipedia title to QID
            return None

        return entity_id