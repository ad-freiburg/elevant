from typing import List, Iterator, Tuple, Dict, Set, Optional

import pickle
import logging
import lmdb

from elevant import settings
from elevant.models.database import Database
from elevant.models.gender import Gender


logger = logging.getLogger("main." + __name__.split(".")[-1])


class EntityDatabaseReader:
    @staticmethod
    def get_link_frequencies() -> Dict[str, Dict[str, int]]:
        filename = settings.LINK_FREEQUENCIES_FILE
        logger.info("Loading link frequencies from %s ..." % filename)
        with open(filename, "rb") as f:
            link_frequencies = pickle.load(f)
        logger.info("-> %d link texts with link frequencies loaded." % len(link_frequencies))
        return link_frequencies

    @staticmethod
    def read_whitelist_types(whitelist_file: Optional[str] = settings.WHITELIST_FILE,
                             with_adjustments: Optional[bool] = False) -> Dict[str, str]:
        logger.info("Loading whitelist types from %s ..." % whitelist_file)
        types = dict()
        adjustments = dict()
        if with_adjustments:
            adjustments = EntityDatabaseReader.read_whitelist_type_adjustments()
        with open(whitelist_file, "r", encoding="utf8") as file:
            for line in file:
                line = line.strip("\n")
                if line:
                    lst = line.split("\t")
                    entity_id = lst[0].strip()
                    if "REPLACE_WITH" in adjustments and entity_id in adjustments["REPLACE_WITH"]:
                        # Ignore whitelist types that occur on the left side of a REPLACE_WITH type adjustment
                        continue
                    name = lst[1].strip()
                    types[entity_id] = name
        logger.info("-> %d whitelist types loaded." % len(types))
        return types

    @staticmethod
    def read_whitelist_type_adjustments(adjustments_file: Optional[str] = settings.WHITELIST_TYPE_ADJUSTMENTS_FILE)\
            -> Dict[str, Dict[str, str]]:
        logger.info("Loading whitelist type adjustments from %s ..." % adjustments_file)
        adjustments = dict()
        with open(adjustments_file, "r", encoding="utf8") as file:
            for line in file:
                line = line.strip()
                if line:
                    lst = line.split("#")
                    type1, rel, type2 = lst[0].strip().split()
                    if rel not in ["MINUS", "REPLACE_WITH"]:
                        logger.warning("Type adjustment relation not known: %s" % rel)
                        continue
                    if rel not in adjustments:
                        adjustments[rel] = {}
                    adjustments[rel][type1.strip()] = type2.strip()
        logger.info("-> Whitelist type adjustments loaded.")
        return adjustments

    @staticmethod
    def get_gender_mapping(mappings_file: str = settings.QID_TO_GENDER_FILE) -> Dict[str, Gender]:
        logger.info("Loading gender mapping from %s ..." % mappings_file)
        mapping = {}
        for i, line in enumerate(open(mappings_file)):
            entity_id, gender_label = line.strip('\n').split('\t')
            gender_tokens = gender_label.split()
            if "female" in gender_tokens:
                mapping[entity_id] = Gender.FEMALE
            elif "male" in gender_tokens:
                mapping[entity_id] = Gender.MALE
            else:
                mapping[entity_id] = Gender.OTHER
        logger.info("-> %d gender mappings loaded." % len(mapping))
        return mapping

    @staticmethod
    def read_human_names() -> Iterator[Tuple[str, str]]:
        filename = settings.QID_TO_HUMAN_NAME_FILE
        logger.info("Yielding given name mapping from %s ..." % filename)
        for line in open(filename):
            entity_id, name = line.strip('\n').split('\t')
            yield entity_id, name

    @staticmethod
    def get_coreference_types_mapping(mappings_file: str = settings.QID_TO_COREF_TYPES_FILE) -> Dict[str, List[str]]:
        logger.info("Loading coreference types from %s ..." % mappings_file)
        mapping = {}
        for i, line in enumerate(open(mappings_file)):
            line = line[:-1]
            entity_id, types = line.split("\t")
            mapping[entity_id] = types.split(";")
        logger.info("-> %d coreference type mappings loaded." % len(mapping))
        return mapping

    @staticmethod
    def get_unigram_counts() -> Dict[str, int]:
        filename = settings.UNIGRAMS_FILE
        logger.info("Loading unigram counts from %s ..." % filename)
        counts = {}
        with open(filename) as f:
            for line in f:
                unigram, count = line.split()
                counts[unigram] = int(count)
        logger.info("-> %d unigram counts loaded." % len(counts))
        return counts

    @staticmethod
    def get_demonyms() -> Dict[str, List[str]]:
        filename = settings.QID_TO_DEMONYM_FILE
        logger.info("Loading demonyms from %s ..." % filename)
        demonyms = {}
        with open(filename) as f:
            for line in f:
                entity_id, demonym = line.strip('\n').split('\t')
                if demonym not in demonyms:
                    demonyms[demonym] = []
                if demonym + "s" not in demonyms:
                    demonyms[demonym + "s"] = []
                demonyms[demonym].append(entity_id)
                demonyms[demonym + "s"].append(entity_id)
        logger.info("-> %d demonyms loaded" % len(demonyms))
        return demonyms

    @staticmethod
    def get_languages() -> Dict[str, str]:
        filename = settings.QID_TO_LANGUAGE_FILE
        logger.info("Loading languages from %s ..." % filename)
        languages = {}
        with open(filename, "r", encoding="utf8") as f:
            for line in f:
                entity_id, language = line.strip('\n').split('\t')
                languages[language] = entity_id
        logger.info("-> %d languages loaded." % len(languages))
        return languages

    @staticmethod
    def get_real_numbers() -> Set[str]:
        filename = settings.QUANTITY_FILE
        logger.info("Loading real numbers from %s ..." % filename)
        real_numbers = EntityDatabaseReader.read_into_set(filename)
        logger.info("-> %d real numbers loaded." % len(real_numbers))
        return real_numbers

    @staticmethod
    def get_points_in_time() -> Set[str]:
        filename = settings.DATETIME_FILE
        logger.info("Loading points in time from %s ..." % filename)
        points_in_time = EntityDatabaseReader.read_into_set(filename)
        logger.info("-> %d points in time loaded." % len(points_in_time))
        return points_in_time

    @staticmethod
    def get_wikipedia_id2wikipedia_title_mapping() -> Dict[int, str]:
        filename = settings.WIKIPEDIA_ID_TO_TITLE_FILE
        logger.info("Loading Wikipedia ID to Wikipedia title mapping from %s ..." % filename)
        wikipedia_id2_wikipedia_title = dict()
        with open(filename) as f:
            for line in f:
                wikipedia_id, title = line.strip('\n').split("\t")
                wikipedia_id = int(wikipedia_id)
                wikipedia_id2_wikipedia_title[wikipedia_id] = title
        logger.info("-> %d Wikipedia ID to Wikipedia title mappings loaded." % len(wikipedia_id2_wikipedia_title))
        return wikipedia_id2_wikipedia_title

    @staticmethod
    def get_instance_of_mapping(relevant_entities=None):
        filename = settings.QID_TO_INSTANCE_OF_FILE
        logger.info("Loading instance-of mapping from %s ..." % filename)
        if relevant_entities:
            logger.info("Loading restricted to %d relevant entities." % len(relevant_entities))
        mapping = EntityDatabaseReader.read_item_to_qid_set_mapping(filename, relevant_entities)
        logger.info("-> %d instance-of mappings loaded." % len(mapping))
        return mapping

    @staticmethod
    def get_subclass_of_mapping(relevant_entities=None):
        filename = settings.QID_TO_SUBCLASS_OF_FILE
        logger.info("Loading subclass-of mapping from %s" % filename)
        if relevant_entities:
            logger.info("Loading restricted to %d relevant entities." % len(relevant_entities))
        mapping = EntityDatabaseReader.read_item_to_qid_set_mapping(filename, relevant_entities)
        logger.info("-> %d subclass-of mappings loaded." % len(mapping))
        return mapping

    @staticmethod
    def get_coarse_types():
        filename = settings.COARSE_TYPES
        logger.info("Loading coarse types from %s" % filename)
        coarse_types = EntityDatabaseReader.read_into_set(filename)
        logger.info("-> %d coarse types loaded." % len(coarse_types))
        return coarse_types

    @staticmethod
    def read_item_to_qid_set_mapping(mapping_file: str, relevant_items):
        mapping = {}
        with open(mapping_file) as f:
            for line in f:
                key, value = line.strip('\n').split('\t')
                if not relevant_items or key in relevant_items:
                    # Could also be "unknown value" in Wikidata which yields sth like _:134b940e46468ab95602a542cefecb52
                    if value and value[0] == "Q":
                        if key not in mapping:
                            mapping[key] = set()
                        mapping[key].add(value)
        return mapping

    @staticmethod
    def read_into_set(file: str):
        new_set = set()
        with open(file) as f:
            for line in f:
                item = line.strip('\n')
                new_set.add(item)
        return new_set

    @staticmethod
    def read_from_dbm(db_file: str, value_type: Optional[type] = str, separator: Optional[str] = ",") -> Database:
        db = Database(db_file, value_type, separator)
        return db

    @staticmethod
    def get_redirects_db() -> Database:
        filename = settings.REDIRECTS_DB
        logger.info(f"Loading redirects database from {filename} ...")
        redirects_db = EntityDatabaseReader.read_from_dbm(filename)
        logger.info(f"-> {len(redirects_db)} redirects loaded.")
        return redirects_db

    @staticmethod
    def get_wikipedia_to_wikidata_db() -> Database:
        filename = settings.WIKIPEDIA_NAME_TO_QID_DB
        logger.info(f"Loading Wikipedia to Wikidata database from {filename} ...")
        wikipedia_to_wikidata_db = EntityDatabaseReader.read_from_dbm(filename)
        logger.info(f"-> {len(wikipedia_to_wikidata_db)} Wikipedia-Wikidata mappings loaded.")
        return wikipedia_to_wikidata_db

    @staticmethod
    def get_entity_name_db() -> Database:
        filename = settings.QID_TO_LABEL_DB
        logger.info(f"Loading entity ID to name database from {filename} ...")
        name_db = EntityDatabaseReader.read_from_dbm(filename)
        logger.info(f"-> {len(name_db)} entity ID to name mappings loaded.")
        return name_db

    @staticmethod
    def get_whitelist_types_db(filename: Optional[str] = settings.QID_TO_WHITELIST_TYPES_DB) -> Database:
        logger.info(f"Loading entity ID to whitelist types database from {filename} ...")
        whitelist_type_db = EntityDatabaseReader.read_from_dbm(filename, value_type=list)
        logger.info(f"-> {len(whitelist_type_db)} entity ID to whitelist types mappings loaded.")
        return whitelist_type_db

    @staticmethod
    def get_sitelink_db() -> Database:
        filename = settings.QID_TO_SITELINKS_DB
        logger.info(f"Loading entity ID to sitelink count database from {filename} ...")
        sitelinks_db = EntityDatabaseReader.read_from_dbm(filename, value_type=int)
        logger.info(f"-> {len(sitelinks_db)} entity ID to sitelink count mappings loaded.")
        return sitelinks_db

    @staticmethod
    def get_entity_to_aliases_db(filename: Optional[str] = settings.QID_TO_ALIASES_DB) -> Database:
        logger.info(f"Loading entity ID to aliases database from {filename} ...")
        aliases_db = EntityDatabaseReader.read_from_dbm(filename, value_type=set, separator=";")
        logger.info(f"-> {len(aliases_db)} entity ID to aliases mappings loaded.")
        return aliases_db

    @staticmethod
    def get_alias_to_entities_db(filename: Optional[str] = settings.ALIAS_TO_QIDS_DB) -> Database:
        logger.info(f"Loading alias to entity IDs database from {filename} ...")
        aliases_db = EntityDatabaseReader.read_from_dbm(filename, value_type=set)
        logger.info(f"-> {len(aliases_db)} alias to entity IDs mappings loaded.")
        return aliases_db

    @staticmethod
    def get_hyperlink_to_most_popular_candidates_db(filename: Optional[str] =
                                                  settings.HYPERLINK_TO_MOST_POPULAR_CANDIDATES_DB) -> Database:
        logger.info(f"Loading hyperlink to most popular entity IDs database from {filename} ...")
        hyperlink_aliases_db = EntityDatabaseReader.read_from_dbm(filename, value_type=set)
        logger.info(f"-> {len(hyperlink_aliases_db)} hyperlink to most popular entity IDs mappings loaded.")
        return hyperlink_aliases_db

    @staticmethod
    def get_name_to_entities_db() -> Database:
        filename = settings.LABEL_TO_QIDS_DB
        logger.info(f"Loading name to entity ID database from {filename} ...")
        name_db = EntityDatabaseReader.read_from_dbm(filename, value_type=set)
        logger.info(f"-> {len(name_db)} name to entity ID mappings loaded.")
        return name_db

    @staticmethod
    def get_entity_name_mapping(filename: str) -> Dict[str, str]:
        logger.info("Loading entity ID to name mapping from %s ..." % filename)
        entity_to_name = {}
        for line in open(filename, "r", encoding="utf8"):
            entity_id, name = line.strip('\n').split('\t')
            entity_to_name[entity_id] = name
        logger.info(f"-> {len(entity_to_name)} entity ID to name mappings loaded.")
        return entity_to_name

    @staticmethod
    def get_entity_types_mapping(filename: str) -> Dict[str, List[str]]:
        logger.info("Loading entity ID to types mapping from %s ..." % filename)
        entity_to_types = {}
        for line in open(filename, "r", encoding="utf8"):
            lst = line.strip('\n').split('\t')
            entity_id = lst[0]
            entity_to_types[entity_id] = lst[1:]
        logger.info(f"-> {len(entity_to_types)} entity ID to types mappings loaded.")
        return entity_to_types
