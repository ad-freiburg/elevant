from enum import Enum
from typing import Dict, Set, Tuple, Iterator, Optional, List, Any

import logging

from src import settings
from src.models.gender import Gender
from src.models.wikidata_entity import WikidataEntity
from src.helpers.entity_database_reader import EntityDatabaseReader

logger = logging.getLogger("main." + __name__.split(".")[-1])


class MappingName(Enum):
    NAME_ALIASES = "name_aliases"
    LINK_ALIASES = "link_aliases"
    WIKIDATA_ALIASES = "wikidata_aliases"
    TITLE_SYNONYMS = "title_synonyms"
    AKRONYMS = "akronyms"
    SITELINKS = "sitelinks"
    ENTITIES = "entities"
    WIKIPEDIA_WIKIDATA = "wikipedia_wikidata"
    REDIRECTS = "redirects"
    LINK_FREQUENCIES = "link_frequencies"
    GENDER = "gender"
    COREFERENCE_TYPES = "coreference_types"
    LANGUAGES = "languages"
    DEMONYMS = "demonyms"
    NAMES = "names"
    WIKIPEDIA_ID_WIKIPEDIA_TITLE = "wikipedia_id_wikipedia_title"


class LoadingType(Enum):
    FULL = "full"
    RELEVANT_ENTITIES = "relevant_entities"
    RESTRICTED = "restricted"


class LoadedInfo:
    def __init__(self, loading_type: LoadingType, info: Optional[Any] = None):
        self.loading_type = loading_type
        self.info = info


class EntityDatabase:
    def __init__(self):
        self.entities = {}
        self.entities: Dict[str, WikidataEntity]
        self.entities_by_name = {}
        self.entities_by_name: Dict[str, Set[str]]
        self.aliases = {}
        self.aliases: Dict[str, Set[str]]
        self.wikipedia2wikidata = {}
        self.wikipedia2wikidata: Dict[str, str]
        self.wikidata2wikipedia = {}
        self.wikidata2wikipedia: Dict[str, str]
        self.redirects = {}
        self.redirects: Dict[str, str]
        self.title_synonyms = {}
        self.title_synonyms: Dict[str, Set[str]]
        self.akronyms = {}
        self.akronyms: Dict[str, Set[str]]
        self.link_frequencies = {}
        self.link_frequencies: Dict[str, Tuple[str, int]]
        self.entity_frequencies = {}
        self.entity_frequencies: Dict[str, int]
        self.entity2gender = {}
        self.entity2gender: Dict[str, Gender]
        self.given_names = {}
        self.given_names: Dict[str, str]
        self.family_names = {}
        self.family_names: Dict[str, str]
        self.entity2coreference_types = {}
        self.entity2coreference_types: Dict[str, List[str]]
        self.unigram_counts = {}
        self.sitelink_counts = {}
        self.demonyms = {}
        self.languages = {}
        self.quantities = set()
        self.datetimes = set()
        self.wikipedia_id2wikipedia_title = dict()
        self.loaded_info = {}

    def add_entity(self, entity: WikidataEntity):
        self.entities[entity.entity_id] = entity
        if entity.name not in self.entities_by_name:
            self.entities_by_name[entity.name] = {entity.entity_id}
        else:
            self.entities_by_name[entity.name].add(entity.entity_id)

    def contains_entity(self, entity_id: str) -> bool:
        return entity_id in self.entities

    def contains_entity_name(self, entity_name: str) -> bool:
        return entity_name in self.entities_by_name

    def get_entities_by_name(self, entity_name: str) -> Set[str]:
        return self.entities_by_name[entity_name]

    def get_entity(self, entity_id: str) -> WikidataEntity:
        return self.entities[entity_id]

    def load_all_entities_in_wikipedia(self, minimum_sitelink_count: Optional[int] = 0,
                                       type_mapping: Optional[str] = settings.WHITELIST_TYPE_MAPPING):
        logger.info("Loading entities from Wikipedia to Wikidata mapping into entity database ...")
        mapping = EntityDatabaseReader.get_wikipedia_to_wikidata_mapping()
        entity_ids = set(mapping.values())
        self.load_entities(entity_ids, minimum_sitelink_count, type_mapping)

    def load_entities(self, entity_ids: Set[str], minimum_sitelink_count: Optional[int] = 0,
                      type_mapping: Optional[str] = settings.WHITELIST_TYPE_MAPPING):
        self.loaded_info[MappingName.ENTITIES] = LoadedInfo(LoadingType.RELEVANT_ENTITIES,
                                                            minimum_sitelink_count)
        logger.info("Loading %d relevant entities with sitelink count >= %d into entity database ..."
                    % (len(entity_ids), minimum_sitelink_count))
        entities = EntityDatabaseReader.get_wikidata_entities_with_types(entity_ids, type_mapping)
        if minimum_sitelink_count > 0:
            # If a minimum sitelink count is given, load sitelink mapping to check
            # entity sitelink counts against the given minimum sitelink count
            self.load_sitelink_counts(minimum_sitelink_count)
        for entity in entities.values():
            if minimum_sitelink_count == 0 or minimum_sitelink_count <= self.get_sitelink_count(entity.entity_id):
                self.add_entity(entity)
        logger.info("-> Entity database contains %d entities." % self.size_entities())

    def size_entities(self) -> int:
        return len(self.entities)

    def add_alias(self, alias: str, entity_id: str):
        if alias not in self.aliases:
            self.aliases[alias] = {entity_id}
        else:
            self.aliases[alias].add(entity_id)
        self.entities[entity_id].synonyms.add(alias)

    def add_wikidata_aliases(self):
        logger.info("Loading Wikidata aliases into entity database ...")
        self.loaded_info[MappingName.WIKIDATA_ALIASES] = LoadedInfo(LoadingType.FULL)
        alias_mapping = EntityDatabaseReader.read_wikidata_aliases()
        for entity_id in self.entities:
            if entity_id in alias_mapping:
                aliases = alias_mapping[entity_id]
                for alias in aliases:
                    self.add_alias(alias, entity_id)
        logger.info("-> Entity database contains %d aliases." % self.size_aliases())

    def add_name_aliases(self):
        logger.info("Loading family name aliases into entity database ...")
        self.loaded_info[MappingName.NAME_ALIASES] = LoadedInfo(LoadingType.FULL)
        for entity_id, name in EntityDatabaseReader.read_names():
            if self.contains_entity(entity_id) and " " in name:
                family_name = name.split()[-1]
                self.add_alias(family_name, entity_id)
        logger.info("-> Entity database contains %d aliases" % self.size_aliases())

    def size_aliases(self) -> int:
        return len(self.aliases)

    def contains_alias(self, alias: str) -> bool:
        return alias in self.aliases

    def load_wikipedia_wikidata_mapping(self):
        logger.info("Loading Wikipedia to Wikidata mapping into entity database ...")
        mapping = EntityDatabaseReader.get_wikipedia_to_wikidata_mapping()
        for entity_name in mapping:
            entity_id = mapping[entity_name]
            self.wikipedia2wikidata[entity_name] = entity_id
            self.wikidata2wikipedia[entity_id] = entity_name
        logger.info("-> Entity database contains %d mappings from Wikipedia to Wikidata and %d mappings from Wikidata"
                    "to Wikipedia" % (len(self.wikipedia2wikidata), len(self.wikidata2wikipedia)))

    def is_wikipedia_wikidata_mapping_loaded(self) -> bool:
        return len(self.wikidata2wikipedia) > 0 and len(self.wikipedia2wikidata) > 0

    def load_redirects(self):
        logger.info("Loading redirects into entity database ...")
        self.redirects = EntityDatabaseReader.get_link_redirects()
        logger.info("-> Redirects loaded into entity database.")

    def is_redirects_loaded(self) -> bool:
        return len(self.redirects) > 0

    def load_title_synonyms(self):
        logger.info("Loading title synonyms into entity database ...")
        self.title_synonyms = EntityDatabaseReader.get_title_synonyms()
        if not self.entities:
            logger.warning("Entity database does not contain any entities. Title synonyms will not be added.")
        for synonym, entity_set in self.title_synonyms.items():
            for entity_title in entity_set:
                entity_id = self.link2id(entity_title)
                if entity_id is not None and self.contains_entity(entity_id):
                    self.entities[entity_id].add_title_synonym(synonym)
        logger.info("-> Title synonyms loaded into entity database.")

    def is_title_synonyms_loaded(self) -> bool:
        return len(self.title_synonyms) > 0

    def load_akronyms(self):
        logger.info("Loading akronyms into entity database ...")
        self.akronyms = EntityDatabaseReader.get_akronyms()
        if not self.entities:
            logger.warning("Entity database does not contain any entities. Akronyms will not be added.")
        for akronym, entity_set in self.akronyms.items():
            for entity_title in entity_set:
                entity_id = self.link2id(entity_title)
                if entity_id is not None and self.contains_entity(entity_id):
                    self.entities[entity_id].add_akronym(akronym)
        logger.info("-> Akronyms loaded into entity database.")

    def is_akronyms_loaded(self) -> bool:
        return len(self.akronyms) > 0

    def link2id(self, link_target: str) -> Optional[str]:
        link_target_variants = [link_target]
        if link_target and link_target[0].islower():
            # In Wikipedia, links that start with a lowercase first letter are automatically redirected to the same link
            # that starts with a capital letter. So there probably won't exist redirect pages for such cases.
            link_target_variants.append(link_target[0].upper() + link_target[1:])
        for target in link_target_variants:
            if target in self.wikipedia2wikidata:
                return self.wikipedia2wikidata[target]
            elif target in self.redirects and self.redirects[target] in self.wikipedia2wikidata:
                return self.wikipedia2wikidata[self.redirects[target]]
        return None

    def id2wikipedia_name(self, entity_id: str) -> str:
        if entity_id in self.wikidata2wikipedia:
            return self.wikidata2wikipedia[entity_id]

    def _iterate_link_frequencies(self) -> Iterator[Tuple[str, str, int]]:
        link_frequencies = EntityDatabaseReader.get_link_frequencies()
        for link_text in link_frequencies:
            for link_target in link_frequencies[link_text]:
                entity_id = self.link2id(link_target)
                if entity_id is not None and self.contains_entity(entity_id):
                    frequency = link_frequencies[link_text][link_target]
                    yield link_text, entity_id, frequency

    def add_link_aliases(self):
        logger.info("Loading link aliases into entity database ...")
        self.loaded_info[MappingName.LINK_ALIASES] = LoadedInfo(LoadingType.FULL)
        for link_text, entity_id, frequency in self._iterate_link_frequencies():
            self.add_alias(link_text, entity_id)
        logger.info("-> Entity database contains %d aliases." % self.size_aliases())

    def load_link_frequencies(self):
        logger.info("Loading link frequencies into entity database ...")
        for link_text, entity_id, frequency in self._iterate_link_frequencies():
            if link_text not in self.link_frequencies:
                self.link_frequencies[link_text] = {}
            if entity_id not in self.link_frequencies[link_text]:
                self.link_frequencies[link_text][entity_id] = frequency
            else:
                self.link_frequencies[link_text][entity_id] += frequency
            if entity_id not in self.entity_frequencies:
                self.entity_frequencies[entity_id] = frequency
            else:
                self.entity_frequencies[entity_id] += frequency
        logger.info("-> Link frequencies loaded into entity database.")

    def is_link_frequencies_loaded(self) -> bool:
        return len(self.link_frequencies) > 0

    def get_candidates(self, alias: str) -> Set[str]:
        if alias not in self.aliases:
            return set()
        else:
            return self.aliases[alias]

    def get_link_frequency(self, alias: str, entity_id: str) -> int:
        if alias not in self.link_frequencies or entity_id not in self.link_frequencies[alias]:
            return 0
        return self.link_frequencies[alias][entity_id]

    def get_alias_frequency(self, alias: str) -> int:
        frequency = 0
        for entity_id in self.get_candidates(alias):
            frequency += self.get_link_frequency(alias, entity_id)
        return frequency

    def get_entity_frequency(self, entity_id: str) -> int:
        return self.entity_frequencies[entity_id] if entity_id in self.entity_frequencies else 0

    def load_gender(self):
        logger.info("Loading gender mapping into entity database ...")
        self.entity2gender = EntityDatabaseReader.get_gender_mapping()
        logger.info("-> Gender mapping loaded into entity database.")

    def is_gender_loaded(self) -> bool:
        return len(self.entity2gender) > 0

    def get_gender(self, entity_id: str) -> Gender:
        if len(self.entity2gender) == 0:
            logger.warning("Tried to access gender information but gender mapping was not loaded.")
        elif entity_id in self.entity2gender:
            return self.entity2gender[entity_id]
        else:
            return Gender.NEUTRAL

    def load_names(self):
        logger.info("Loading family and given names into entity database ...")
        for entity_id, name in EntityDatabaseReader.read_names():
            if " " in name:
                given_name = name.split()[0]
                family_name = name.split()[-1]
                if len(given_name) > 1:
                    self.given_names[entity_id] = given_name
                if len(family_name) > 1:
                    self.family_names[entity_id] = family_name
        logger.info("-> Family and given names loaded.")

    def is_names_loaded(self) -> bool:
        return len(self.given_names) > 0 and len(self.family_names) > 0

    def has_given_name(self, entity_id: str) -> bool:
        if len(self.given_names) == 0:
            logger.warning("Tried to access first names mapping but first name mapping was not loaded.")
        if entity_id in self.given_names:
            return True
        return False

    def get_given_name(self, entity_id: str) -> str:
        return self.given_names[entity_id]

    def has_family_name(self, entity_id: str) -> bool:
        if len(self.family_names) == 0:
            logger.warning("Tried to access family names mapping but family name mapping was not loaded.")
        if entity_id in self.family_names:
            return True
        return False

    def get_family_name(self, entity_id: str) -> str:
        return self.family_names[entity_id]

    def load_coreference_types(self):
        logger.info("Loading coreference types into entity database...")
        self.entity2coreference_types = EntityDatabaseReader.get_coreference_types_mapping()
        logger.info("-> Coreference types loaded into entity database.")

    def is_coreference_types_loaded(self) -> bool:
        return len(self.entity2coreference_types) > 0

    def has_coreference_types(self, entity_id: str) -> bool:
        return entity_id in self.entity2coreference_types

    def get_coreference_types(self, entity_id: str) -> List[str]:
        return self.entity2coreference_types[entity_id]

    def load_unigram_counts(self):
        logger.info("Loading unigram counts into entity database...")
        self.unigram_counts = EntityDatabaseReader.get_unigram_counts()
        logger.info("-> Unigram counts loaded into entity database.")

    def get_unigram_count(self, token: str) -> int:
        if token not in self.unigram_counts:
            return 0
        return self.unigram_counts[token]

    def load_sitelink_counts(self, min_count: Optional[int] = 1):
        logger.info("Loading sitelink counts >= %d into entity database ..." % min_count)
        loading_type = LoadingType.RESTRICTED if min_count > 0 else LoadingType.FULL
        self.loaded_info[MappingName.SITELINKS] = LoadedInfo(loading_type, min_count)
        self.sitelink_counts = EntityDatabaseReader.get_sitelink_counts(min_count)
        logger.info("-> Sitelink counts loaded into entity database.")

    def has_sitelink_counts_loaded(self) -> bool:
        return len(self.sitelink_counts) > 0

    def get_sitelink_count(self, entity_id: str) -> int:
        if not self.has_sitelink_counts_loaded():
            logger.warning("Tried to access sitelink counts, but sitelink counts were not loaded.")
        return self.sitelink_counts[entity_id] if entity_id in self.sitelink_counts else 0

    def load_demonyms(self):
        logger.info("Loading demonyms into entity database ...")
        self.demonyms = EntityDatabaseReader.get_demonyms()
        logger.info("-> Demonyms loaded into entity database.")

    def has_demonyms_loaded(self) -> bool:
        return len(self.demonyms) > 0

    def is_demonym(self, text: str) -> bool:
        if not self.has_demonyms_loaded():
            logger.warning("Tried to access demonyms, but demonyms were not loaded.")
        return text in self.demonyms

    def get_entities_for_demonym(self, demonym: str) -> List[str]:
        return self.demonyms[demonym]

    def load_languages(self):
        logger.info("Loading languages into entity database ...")
        self.languages = EntityDatabaseReader.get_languages()
        logger.info("-> Languages loaded into entity database.")

    def has_languages_loaded(self) -> bool:
        return len(self.languages) > 0

    def is_language(self, text: str) -> bool:
        if not self.has_languages_loaded():
            logger.warning("Tried to access languages, but languages were not loaded.")
        return text in self.languages

    def get_entity_for_language(self, language: str) -> str:
        return self.languages[language]

    def load_quantities(self):
        logger.info("Loading quantities into entity database ...")
        self.quantities = EntityDatabaseReader.get_real_numbers()
        logger.info("-> Quantities loaded into entity database.")

    def has_quantities_loaded(self) -> bool:
        return len(self.quantities) > 0

    def is_quantity(self, entity_id: str) -> bool:
        if not self.has_quantities_loaded():
            logger.warning("Tried to access quantities, but quantities were not loaded.")
        return entity_id in self.quantities

    def load_datetimes(self):
        logger.info("Loading datetimes into entity database ...")
        self.datetimes = EntityDatabaseReader.get_points_in_time()
        logger.info("-> Datetimes loaded into entity database.")

    def has_datetimes_loaded(self) -> bool:
        return len(self.datetimes) > 0

    def is_datetime(self, entity_id: str) -> bool:
        if not self.has_datetimes_loaded():
            logger.warning("Tried to access datetimes, but datetimes were not loaded.")
        return entity_id in self.datetimes

    def load_wikipedia_id2wikipedia_title(self):
        logger.info("Loading Wikipedia ID to Wikipedia title into entity database ...")
        self.wikipedia_id2wikipedia_title = EntityDatabaseReader.get_wikipedia_id2wikipedia_title_mapping()
        logger.info("-> Wikipedia ID to Wikipedia title mapping loaded into entity database. ")

    def has_wikipedia_id2wikipedia_title_loaded(self) -> bool:
        return len(self.wikipedia_id2wikipedia_title) > 0

    def get_wikipedia_title_by_wikipedia_id(self, wikipedia_id: int) -> Optional[str]:
        if not self.has_wikipedia_id2wikipedia_title_loaded():
            logger.warning("Tried to access wikipedia title to wikipedia id mapping, but mapping was not loaded.")
        if wikipedia_id in self.wikipedia_id2wikipedia_title:
            return self.wikipedia_id2wikipedia_title[wikipedia_id]
        return None
