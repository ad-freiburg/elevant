from enum import Enum
from typing import Dict, Set, Tuple, Iterator, Optional, List, Any

import logging

from elevant import settings
from elevant.evaluation.groundtruth_label import GroundtruthLabel
from elevant.models.database import Database
from elevant.models.gender import Gender
from elevant.helpers.entity_database_reader import EntityDatabaseReader

logger = logging.getLogger("main." + __name__.split(".")[-1])


class MappingName(Enum):
    WIKIDATA_ALIASES = "wikidata_aliases"
    FAMILY_NAME_ALIASES = "family_name_aliases"
    LINK_ALIASES = "link_aliases"
    SITELINKS = "sitelinks"
    ENTITIES = "entities"
    WIKIPEDIA_WIKIDATA = "wikipedia_wikidata"
    REDIRECTS = "redirects"
    LINK_FREQUENCIES = "link_frequencies"
    GENDER = "gender"
    COREFERENCE_TYPES = "coreference_types"
    LANGUAGES = "languages"
    DEMONYMS = "demonyms"
    WIKIPEDIA_ID_WIKIPEDIA_TITLE = "wikipedia_id_wikipedia_title"
    NAME_TO_ENTITY_ID = "name_to_entity_id"
    ENTITY_ID_TO_ALIAS = "entity_id_to_alias"
    ENTITY_ID_TO_FAMILY_NAME = "entity_id_to_family_name"
    ENTITY_ID_TO_LINK_ALIAS = "entity_id_to_link_alias"
    HYPERLINK_TO_MOST_POPULAR_CANDIDATES = "hyperlink_alias_to_most_popular_candidates"


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
        self.entities = set()
        self.entities: Set[str]
        self.name_to_entities_db = {}
        self.name_to_entities_db: Dict[str, Set[str]]
        self.entity_type_db = {}
        self.entity_type_db: Database
        self.entity_name_db = {}
        self.entity_name_db: Database
        self.alias_to_entities_db = {}
        self.alias_to_entities_db: Database
        self.family_name_aliases = {}
        self.family_name_aliases: Dict[str, Set[str]]
        self.link_aliases = {}
        self.link_aliases: Dict[str, Set[str]]
        self.entity_to_aliases_db = {}
        self.entity_to_aliases_db: Database
        self.entity_to_family_name = {}
        self.entity_to_family_name: Dict[str, str]
        self.entity_to_link_alias = {}
        self.entity_to_link_alias: Dict[str, Set[str]]
        self.aliases = {}
        self.aliases: Dict[str, Set[str]]
        self.wikipedia2wikidata = {}
        self.wikipedia2wikidata: Database
        self.wikidata2wikipedia = {}
        self.wikidata2wikipedia: Dict[str, str]
        self.redirects = {}
        self.redirects: Database
        self.link_frequencies = {}
        self.link_frequencies: Dict[str, Dict[str, int]]
        self.entity_frequencies = {}
        self.entity_frequencies: Dict[str, int]
        self.hyperlink_to_most_popular_candidates_db = {}
        self.hyperlink_to_most_popular_candidates_db: Database
        self.entity2gender = {}
        self.entity2gender: Dict[str, Gender]
        self.entity2coreference_types = {}
        self.entity2coreference_types: Dict[str, List[str]]
        self.unigram_counts = {}
        self.sitelink_counts = {}
        self.demonyms = {}
        self.languages = {}
        self.quantities = set()
        self.datetimes = set()
        self.wikipedia_id2wikipedia_title = dict()
        self.type_adjustments = {}
        self.loaded_info = {}

    def contains_entity(self, entity_id: str) -> bool:
        return entity_id in self.entities

    def load_all_entities_in_wikipedia(self, minimum_sitelink_count: Optional[int] = 0):
        logger.info("Loading entities from Wikipedia to Wikidata mapping into entity database ...")
        self.loaded_info[MappingName.ENTITIES] = LoadedInfo(LoadingType.RELEVANT_ENTITIES,
                                                            minimum_sitelink_count)
        db = EntityDatabaseReader.get_wikipedia_to_wikidata_db()
        entity_ids = set(db.values())
        if minimum_sitelink_count == 0:
            self.entities = entity_ids
        else:
            # If a minimum sitelink count is given, load sitelink mapping to check
            # entity sitelink counts against the given minimum sitelink count
            self.load_sitelink_counts()
            for entity_id in entity_ids:
                if minimum_sitelink_count <= self.get_sitelink_count(entity_id):
                    self.entities.add(entity_id)
        logger.info(f"-> Entity database contains {len(self.entities)} entities.")

    def load_entity_types(self, type_db: Optional[str] = settings.QID_TO_WHITELIST_TYPES_DB):
        if not self.entity_type_db:
            self.entity_type_db = EntityDatabaseReader.get_whitelist_types_db(type_db)
            self.type_adjustments = EntityDatabaseReader.read_whitelist_type_adjustments()
        else:
            logger.info("Entity type database already loaded.")

    def load_custom_entity_types(self, filename: str):
        if not self.entity_type_db:
            self.entity_type_db = EntityDatabaseReader.get_entity_types_mapping(filename)
        else:
            logger.info("Entity type mapping already loaded.")

    def get_entity_types(self, entity_id: str) -> Optional[List[str]]:
        if len(self.entity_type_db) == 0:
            logger.warning("Tried to access entity type database, but entity type database was not loaded.")
            return None
        return self.adjusted_entity_types(entity_id)

    def adjusted_entity_types(self, entity_id: str) -> List[str]:
        if not self.type_adjustments:
            if entity_id in self.entity_type_db:
                return self.entity_type_db[entity_id]
            else:
                return [GroundtruthLabel.OTHER]

        adj_replace = self.type_adjustments["REPLACE_WITH"]
        adj_minus = self.type_adjustments["MINUS"]
        if entity_id in self.entity_type_db:
            whitelist_types = self.entity_type_db[entity_id]
            adjusted_types = []
            for wt in whitelist_types:
                # Perform type adjustments
                adjusted_type = adj_replace[wt] if wt in adj_replace else wt
                if adjusted_type in adj_minus and adj_minus[adjusted_type] in adjusted_types:
                    # Type is left element of minus-rule and right element is already in the entity's type list.
                    # Don't add type.
                    continue
                for t in adjusted_types:
                    if t in adj_minus and adjusted_type == adj_minus[t]:
                        # Type is right element of minus-rule and left element is already in the entity's type list.
                        # Remove previously added type.
                        adjusted_types.remove(t)

                if adjusted_type not in adjusted_types:
                    # Due to the adjustment, the same type might be added twice without this check
                    adjusted_types.append(adjusted_type)

            return adjusted_types
        else:
            return [GroundtruthLabel.OTHER]

    def load_entity_names(self):
        if not self.entity_name_db:
            self.entity_name_db = EntityDatabaseReader.get_entity_name_db()
        else:
            logger.info("Entity name database already loaded.")

    def load_custom_entity_names(self, filename: str):
        if not self.entity_name_db:
            self.entity_name_db = EntityDatabaseReader.get_entity_name_mapping(filename)
        else:
            logger.info("Entity name mapping already loaded.")

    def get_entity_name(self, entity_id: str) -> Optional[str]:
        if len(self.entity_name_db) == 0:
            logger.warning("Tried to access entity name database, but entity name database was not loaded.")
            return None
        return self.entity_name_db[entity_id] if entity_id in self.entity_name_db else "Unknown"

    def load_name_to_entities(self):
        self.loaded_info[MappingName.NAME_TO_ENTITY_ID] = LoadedInfo(LoadingType.FULL)
        if not self.name_to_entities_db:
            self.name_to_entities_db = EntityDatabaseReader.get_name_to_entities_db()
        else:
            logger.info("Entity name to entity IDs database already loaded.")

    def contains_entity_name(self, entity_name: str) -> bool:
        return entity_name in self.name_to_entities_db

    def get_entities_by_name(self, entity_name: str) -> Set[str]:
        return self.name_to_entities_db[entity_name]

    def load_alias_to_entities(self):
        self.loaded_info[MappingName.WIKIDATA_ALIASES] = LoadedInfo(LoadingType.FULL)
        if not self.alias_to_entities_db:
            self.alias_to_entities_db = EntityDatabaseReader.get_alias_to_entities_db()
        else:
            logger.info("Entity aliases database already loaded.")
        # The entity name is also an alias, so load it too.
        self.load_name_to_entities()

    def load_family_name_aliases(self):
        logger.info("Loading family name aliases into entity database ...")
        self.loaded_info[MappingName.FAMILY_NAME_ALIASES] = LoadedInfo(LoadingType.FULL)
        for entity_id, name in EntityDatabaseReader.read_human_names():
            if " " in name:
                family_name = name.split()[-1]
                if family_name in self.family_name_aliases:
                    self.family_name_aliases[family_name].add(entity_id)
                else:
                    self.family_name_aliases[family_name] = {entity_id}
        logger.info(f"-> {len(self.family_name_aliases)} family name aliases loaded into entity database.")

    def load_link_aliases(self, with_frequencies: Optional[bool] = False):
        if with_frequencies:
            logger.info("Loading link aliases and their frequencies into entity database ...")
        else:
            logger.info("Loading link aliases into entity database ...")
        self.loaded_info[MappingName.LINK_ALIASES] = LoadedInfo(LoadingType.FULL)
        for link_text, entity_id, frequency in self._iterate_link_frequencies():
            if link_text in self.link_aliases:
                self.link_aliases[link_text].add(entity_id)
                if with_frequencies:
                    if entity_id not in self.link_frequencies[link_text]:
                        self.link_frequencies[link_text][entity_id] = frequency
                    else:
                        self.link_frequencies[link_text][entity_id] += frequency
            else:
                self.link_aliases[link_text] = {entity_id}
                if with_frequencies:
                    self.link_frequencies[link_text] = {entity_id: frequency}
        if with_frequencies:
            logger.info(f"-> {len(self.link_aliases)} link aliases and their frequencies loaded into entity database.")
        else:
            logger.info(f"-> {len(self.link_aliases)} link aliases loaded into entity database.")

    def load_hyperlink_to_most_popular_candidates(self):
        logger.info("Loading hyperlink to most popular candidates into entity database ...")
        if not self.hyperlink_to_most_popular_candidates_db:
            self.loaded_info[MappingName.HYPERLINK_TO_MOST_POPULAR_CANDIDATES] = LoadedInfo(LoadingType.FULL)
            self.hyperlink_to_most_popular_candidates_db = \
                EntityDatabaseReader.get_hyperlink_to_most_popular_candidates_db(
                    settings.HYPERLINK_TO_MOST_POPULAR_CANDIDATES_DB)
            logger.info(f"-> {len(self.hyperlink_to_most_popular_candidates_db)} "
                        f"hyperlink to most popular candidates mappings loaded into entity database.")
        else:
            logger.info("Hyperlink to most popular candidates database already loaded.")

    def get_most_popular_candidate_for_hyperlink(self, alias: str) -> Set[str]:
        if len(self.hyperlink_to_most_popular_candidates_db) == 0:
            logger.warning("Tried to access hyperlink to most popular candidates database, but db was not loaded.")
        if alias in self.hyperlink_to_most_popular_candidates_db:
            return self.hyperlink_to_most_popular_candidates_db[alias]
        return set()

    def get_candidates(self, alias: str) -> Set[str]:
        entity_ids = set()
        if alias in self.name_to_entities_db:
            entity_ids = entity_ids.union(self.name_to_entities_db[alias])
        if alias in self.alias_to_entities_db:
            entity_ids = entity_ids.union(self.alias_to_entities_db[alias])
        if alias in self.family_name_aliases:
            entity_ids = entity_ids.union(self.family_name_aliases[alias])
        if alias in self.link_aliases:
            entity_ids = entity_ids.union(self.link_aliases[alias])
        return entity_ids

    def contains_alias(self, alias: str) -> bool:
        return alias in self.name_to_entities_db or \
               alias in self.alias_to_entities_db or \
               alias in self.family_name_aliases or \
               alias in self.link_aliases

    def load_entity_to_aliases(self):
        self.loaded_info[MappingName.ENTITY_ID_TO_ALIAS] = LoadedInfo(LoadingType.FULL)
        if not self.entity_to_aliases_db:
            self.entity_to_aliases_db = EntityDatabaseReader.get_entity_to_aliases_db()
        else:
            logger.info("Entity ID to aliases database already loaded.")
        # The entity name is also an alias, so load it too.
        self.load_entity_names()

    def load_entity_to_family_name(self):
        logger.info("Loading entity ID to family name aliases into entity database ...")
        self.loaded_info[MappingName.ENTITY_ID_TO_FAMILY_NAME] = LoadedInfo(LoadingType.FULL)
        for entity_id, name in EntityDatabaseReader.read_human_names():
            if " " in name:
                family_name = name.split()[-1]
                self.entity_to_family_name[entity_id] = family_name
        logger.info(f"-> {len(self.entity_to_family_name)} entity ID to family name aliases "
                    f"loaded into entity database.")

    def load_entity_to_link_aliases(self):
        logger.info("Loading entity ID to link aliases into entity database ...")
        self.loaded_info[MappingName.ENTITY_ID_TO_LINK_ALIAS] = LoadedInfo(LoadingType.FULL)
        for link_text, entity_id, frequency in self._iterate_link_frequencies():
            if link_text in self.entity_to_link_alias:
                self.entity_to_link_alias[entity_id].add(link_text)
            else:
                self.entity_to_link_alias[entity_id] = {link_text}
        logger.info(f"-> {len(self.entity_to_link_alias)} entity ID to link alias mappings loaded into entity "
                    f"database.")

    def get_entity_aliases(self, entity_id: str) -> Optional[Set[str]]:
        aliases = set()
        if entity_id in self.entity_name_db:
            # self.entity_name_db values are strings, not dicts as for the other entity to alias mappings.
            aliases.add(self.entity_name_db[entity_id])
        if entity_id in self.entity_to_aliases_db:
            aliases = aliases.union(self.entity_to_aliases_db[entity_id])
        if entity_id in self.entity_to_family_name:
            aliases.add(self.entity_to_family_name[entity_id])
        if entity_id in self.entity_to_link_alias:
            aliases = aliases.union(self.entity_to_link_alias[entity_id])
        return aliases

    def load_wikipedia_to_wikidata_db(self):
        self.wikipedia2wikidata = EntityDatabaseReader.get_wikipedia_to_wikidata_db()

    def load_wikidata_to_wikipedia_mapping(self):
        self.wikipedia2wikidata = EntityDatabaseReader.get_wikipedia_to_wikidata_db()
        for wikipedia_name, entity_id in self.wikipedia2wikidata.items():
            self.wikidata2wikipedia[entity_id] = wikipedia_name

    def is_wikipedia_to_wikidata_mapping_loaded(self) -> bool:
        return len(self.wikipedia2wikidata) > 0

    def is_wikidata_to_wikipedia_mapping_loaded(self) -> bool:
        return len(self.wikidata2wikipedia) > 0

    def load_redirects(self):
        self.redirects = EntityDatabaseReader.get_redirects_db()

    def is_redirects_loaded(self) -> bool:
        return len(self.redirects) > 0

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
            for entity_id in link_frequencies[link_text]:
                frequency = link_frequencies[link_text][entity_id]
                yield link_text, entity_id, frequency

    def load_link_frequencies(self):
        for link_text, entity_id, frequency in self._iterate_link_frequencies():
            if link_text not in self.link_frequencies:
                self.link_frequencies[link_text] = {}
            if entity_id not in self.link_frequencies[link_text]:
                self.link_frequencies[link_text][entity_id] = frequency
            else:
                # This case can happen, when different link targets map to the same article (e.g. due to redirects)
                self.link_frequencies[link_text][entity_id] += frequency

    def load_entity_frequencies(self):
        for link_text, entity_id, frequency in self._iterate_link_frequencies():
            if entity_id not in self.entity_frequencies:
                self.entity_frequencies[entity_id] = frequency
            else:
                self.entity_frequencies[entity_id] += frequency

    def is_link_frequencies_loaded(self) -> bool:
        return len(self.link_frequencies) > 0

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
        self.entity2gender = EntityDatabaseReader.get_gender_mapping()

    def is_gender_loaded(self) -> bool:
        return len(self.entity2gender) > 0

    def get_gender(self, entity_id: str) -> Gender:
        if len(self.entity2gender) == 0:
            logger.warning("Tried to access gender information but gender mapping was not loaded.")
        elif entity_id in self.entity2gender:
            return self.entity2gender[entity_id]
        else:
            return Gender.NEUTRAL

    def load_coreference_types(self):
        self.entity2coreference_types = EntityDatabaseReader.get_coreference_types_mapping()

    def is_coreference_types_loaded(self) -> bool:
        return len(self.entity2coreference_types) > 0

    def has_coreference_types(self, entity_id: str) -> bool:
        return entity_id in self.entity2coreference_types

    def get_coreference_types(self, entity_id: str) -> List[str]:
        return self.entity2coreference_types[entity_id]

    def load_unigram_counts(self):
        self.unigram_counts = EntityDatabaseReader.get_unigram_counts()

    def get_unigram_count(self, token: str) -> int:
        if token not in self.unigram_counts:
            return 0
        return self.unigram_counts[token]

    def load_sitelink_counts(self):
        if self.loaded_info.get(MappingName.SITELINKS) == LoadedInfo(LoadingType.FULL):
            logger.info("-> Sitelink counts already loaded.")
        else:
            self.loaded_info[MappingName.SITELINKS] = LoadedInfo(LoadingType.FULL)
            self.sitelink_counts = EntityDatabaseReader.get_sitelink_db()

    def has_sitelink_counts_loaded(self) -> bool:
        return len(self.sitelink_counts) > 0

    def get_sitelink_count(self, entity_id: str) -> int:
        if not self.has_sitelink_counts_loaded():
            logger.warning("Tried to access sitelink counts, but sitelink counts were not loaded.")
        return self.sitelink_counts[entity_id] if entity_id in self.sitelink_counts else 0

    def load_demonyms(self):
        self.demonyms = EntityDatabaseReader.get_demonyms()

    def has_demonyms_loaded(self) -> bool:
        return len(self.demonyms) > 0

    def is_demonym(self, text: str) -> bool:
        if not self.has_demonyms_loaded():
            logger.warning("Tried to access demonyms, but demonyms were not loaded.")
        return text in self.demonyms

    def get_entities_for_demonym(self, demonym: str) -> List[str]:
        return self.demonyms[demonym]

    def load_languages(self):
        self.languages = EntityDatabaseReader.get_languages()

    def has_languages_loaded(self) -> bool:
        return len(self.languages) > 0

    def is_language(self, text: str) -> bool:
        if not self.has_languages_loaded():
            logger.warning("Tried to access languages, but languages were not loaded.")
        return text in self.languages

    def get_entity_for_language(self, language: str) -> str:
        return self.languages[language]

    def load_quantities(self):
        self.quantities = EntityDatabaseReader.get_real_numbers()

    def has_quantities_loaded(self) -> bool:
        return len(self.quantities) > 0

    def is_quantity(self, entity_id: str) -> bool:
        if not self.has_quantities_loaded():
            logger.warning("Tried to access quantities, but quantities were not loaded.")
        return entity_id in self.quantities

    def load_datetimes(self):
        self.datetimes = EntityDatabaseReader.get_points_in_time()

    def has_datetimes_loaded(self) -> bool:
        return len(self.datetimes) > 0

    def is_datetime(self, entity_id: str) -> bool:
        if not self.has_datetimes_loaded():
            logger.warning("Tried to access datetimes, but datetimes were not loaded.")
        return entity_id in self.datetimes

    def load_wikipedia_id2wikipedia_title(self):
        self.wikipedia_id2wikipedia_title = EntityDatabaseReader.get_wikipedia_id2wikipedia_title_mapping()

    def has_wikipedia_id2wikipedia_title_loaded(self) -> bool:
        return len(self.wikipedia_id2wikipedia_title) > 0

    def get_wikipedia_title_by_wikipedia_id(self, wikipedia_id: int) -> Optional[str]:
        if not self.has_wikipedia_id2wikipedia_title_loaded():
            logger.warning("Tried to access wikipedia title to wikipedia id mapping, but mapping was not loaded.")
        if wikipedia_id in self.wikipedia_id2wikipedia_title:
            return self.wikipedia_id2wikipedia_title[wikipedia_id]
        return None
