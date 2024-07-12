from enum import Enum
from typing import Optional
from urllib.parse import unquote

import re
import logging

from elevant.models.entity_database import EntityDatabase

logger = logging.getLogger("main." + __name__.split(".")[-1])


class UnknownEntity(Enum):
    NO_MAPPING = "<NO_MAPPING>"
    NIL = "<NIL>"


class KnowledgeBaseName(Enum):
    WIKIDATA = "wikidata"
    WIKIPEDIA = "wikipedia"
    DBPEDIA = "dbpedia"
    UNIDENTIFIED_KB = "unidentified_kb"


class KnowledgeBase:
    def __init__(self, name: KnowledgeBaseName, entity_uri_prefix: str):
        self.name = name
        self.entity_uri_prefix = entity_uri_prefix


class KnowledgeBaseMapper:
    wikidata_kb = KnowledgeBase(KnowledgeBaseName.WIKIDATA, "wikidata.org/")
    wikipedia_kb = KnowledgeBase(KnowledgeBaseName.WIKIPEDIA, "wikipedia.org/")
    dbpedia_kb = KnowledgeBase(KnowledgeBaseName.DBPEDIA, "dbpedia.org/")
    kbs = [wikidata_kb, wikipedia_kb, dbpedia_kb]

    @staticmethod
    def is_unknown_entity(entity_id: str) -> bool:
        return entity_id in (UnknownEntity.NIL.value, UnknownEntity.NO_MAPPING.value)

    @staticmethod
    def identify_kb(entity_uri: str) -> Optional[KnowledgeBaseName]:
        """ Identify the knowledge base in which an entity was referenced from
        the given entity URI.
        """
        if "/notInWiki/" in entity_uri:
            # This is used e.g. in RSS-500 to indicate unknown entities
            return None
        for kb in KnowledgeBaseMapper.kbs:
            # Don't use startswith because it could start with http or https
            if kb.entity_uri_prefix in entity_uri:
                return kb.name
        return KnowledgeBaseName.UNIDENTIFIED_KB

    @staticmethod
    def get_wikidata_qid(entity_reference: str, entity_db: EntityDatabase, verbose: Optional[bool] = False,
                         kb_name: Optional[KnowledgeBaseName] = None)\
            -> Optional[str]:
        """ Given a reference string to an entity and an EntityDatabase with
        the Wikipedia to Wikidata mapping loaded, try to retrieve the Wikidata
        QID of the referenced entity.
        Returns None if the entity can't be mapped to a Wikidata QID
        """
        if not entity_reference:
            return UnknownEntity.NIL.value

        if entity_reference in ("NIL", "<NIL>", "<unk_wid>", "<unk>", "<UNK>"):
            # In the Derczynski dataset, NIL is used as entity reference to indicate NIL entities
            logger.info(f"\"{entity_reference}\" entity reference is interpreted as NIL entity.")
            return UnknownEntity.NIL.value

        # The last part of a URI is the entity name / identifier.
        # This still works if the entity_reference is not a URI and does not contain a "/" (result of rfind is -1)
        entity_name = entity_reference[entity_reference.rfind("/") + 1:]

        if not entity_name:
            logger.info("Empty entity name. Probably a NIL prediction.")
            return UnknownEntity.NIL.value

        # Try to identify the used KB if none was provided
        if kb_name is None:
            kb_name = KnowledgeBaseMapper.identify_kb(entity_reference)

        # If no KB could be inferred, the URI was an out-of-KB URI
        if kb_name is None:
            return UnknownEntity.NIL.value

        if kb_name == KnowledgeBaseName.UNIDENTIFIED_KB and verbose:
            logger.info("Unidentified knowledge base in entity URI: %s. Trying to infer KB from entity name."
                        % entity_reference)

        # Retrieve Wikidata QID based on identified KB or entity name
        if kb_name == KnowledgeBaseName.WIKIDATA or (kb_name == KnowledgeBaseName.UNIDENTIFIED_KB
                                                     and re.match(r"Q[0-9]+", entity_name)):
            entity_id = entity_name
        else:
            if entity_name != entity_reference:
                # Unquote entity name only if it was part of a URI
                entity_name = unquote(entity_name)
            entity_name = entity_name.replace('_', ' ')

            # The Derczynski dataset contains invisible characters which leads to entities not being mapped.
            new_entity_name = ''.join(c for c in entity_name if c.isprintable())
            if new_entity_name != entity_name:
                logger.info("Unprintable characters found in entity name \"%s\". "
                            "These characters are removed to find a mapping to Wikidata." % entity_name)
                entity_name = new_entity_name

            # This should work for both Wikipedia and DBpedia entity names
            # This site contains info about the (very minor) differences between Wikipedia and DBpedia names:
            # http://nl.dbpedia.org/web/infra/uri-encoding
            entity_id = entity_db.link2id(entity_name)
            if not entity_id:
                logger.info("Entity name \"%s\" could not be mapped to a Wikidata QID." % entity_name)
                return UnknownEntity.NO_MAPPING.value

        return entity_id
