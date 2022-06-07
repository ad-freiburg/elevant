from typing import List, Iterator, Tuple, Dict, Set, Optional

from urllib.parse import unquote
import pickle
import logging

from src import settings
from src.evaluation.groundtruth_label import GroundtruthLabel
from src.models.gender import Gender
from src.models.wikidata_entity import WikidataEntity


WIKI_URL_PREFIX = "https://en.wikipedia.org/wiki/"

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
    def get_link_redirects() -> Dict[str, str]:
        filename = settings.REDIRECTS_FILE
        logger.info("Loading redirects from %s ..." % filename)
        with open(filename, "rb") as f:
            redirects = pickle.load(f)
        logger.info("-> %d redirects loaded." % len(redirects))
        return redirects

    @staticmethod
    def get_title_synonyms() -> Dict[str, Set[str]]:
        filename = settings.TITLE_SYNONYMS_FILE
        logger.info("Loading title synonyms from %s ..." % filename)
        with open(filename, "rb") as f:
            title_synonyms = pickle.load(f)
        logger.info("-> %d title synonyms loaded." % len(title_synonyms))
        return title_synonyms

    @staticmethod
    def get_akronyms() -> Dict[str, Set[str]]:
        filename = settings.AKRONYMS_FILE
        logger.info("Loading akronyms from %s ..." % filename)
        with open(filename, "rb") as f:
            akronyms = pickle.load(f)
        logger.info("-> %d akronyms loaded." % len(akronyms))
        return akronyms

    @staticmethod
    def get_wikipedia_to_wikidata_mapping(mappings_file: str = settings.QID_TO_WIKIPEDIA_URL_FILE):
        logger.info("Loading Wikipedia title to Wikidata ID mapping from %s ..." % mappings_file)
        mapping = {}
        for i, line in enumerate(open(mappings_file)):
            entity_id, link_url = line.strip('\n').split('\t')
            link_url = unquote(link_url)
            entity_name = link_url[len(WIKI_URL_PREFIX):].replace('_', ' ')
            mapping[entity_name] = entity_id
        logger.info("-> %d Wikipedia-Wikidata mappings loaded." % len(mapping))
        return mapping

    @staticmethod
    def get_wikidata_entities_with_types(relevant_entities: Set[str],
                                         type_mapping_file: str) -> Dict[str, WikidataEntity]:
        logger.info("Loading Wikidata entity info (types and label) ...")
        entities = dict()
        id_to_type = dict()
        adjustments = EntityDatabaseReader.read_whitelist_type_adjustments()
        adj_replace = adjustments["REPLACE_WITH"]
        adj_minus = adjustments["MINUS"]
        for entity_id, whitelist_type in EntityDatabaseReader.entity_to_whitelist_type_iterator(type_mapping_file):
            if entity_id in relevant_entities:
                if entity_id not in id_to_type:  # An entity can have multiple types from the whitelist
                    id_to_type[entity_id] = []

                # Perform type adjustments
                adjusted_type = adj_replace[whitelist_type] if whitelist_type in adj_replace else whitelist_type
                if adjusted_type in adj_minus and adj_minus[adjusted_type] in id_to_type[entity_id]:
                    # Type is left element of minus-rule and right element is already in the entity's type list.
                    # Don't add type.
                    continue
                for t in id_to_type[entity_id]:
                    if t in adj_minus and adjusted_type == adj_minus[t]:
                        # Type is right element of minus-rule and left element is already in the entity's type list.
                        # Remove previously added type.
                        id_to_type[entity_id].remove(t)

                if adjusted_type not in id_to_type[entity_id]:
                    # Due to the adjustment, the same type might be added twice without this check
                    id_to_type[entity_id].append(adjusted_type)

        id_to_name = dict()
        for entity_id, name in EntityDatabaseReader.entity_to_label_iterator():
            if entity_id in relevant_entities:
                id_to_name[entity_id] = name

        for entity_id in relevant_entities:
            types = GroundtruthLabel.OTHER
            name = "Unknown"
            if entity_id in id_to_type:
                types = "|".join(id_to_type[entity_id])
            if entity_id in id_to_name:
                name = id_to_name[entity_id]
            entity = WikidataEntity(name, 0, entity_id, type=types)
            entities[entity_id] = entity
        logger.info("-> %d entities loaded." % len(entities))
        return entities

    @staticmethod
    def entity_to_label_iterator() -> Iterator[Tuple[str, str]]:
        filename = settings.QID_TO_LABEL_FILE
        logger.info("Yielding label mapping from %s ..." % filename)
        with open(filename, "r", encoding="utf8") as file:
            for line in file:
                entity_id, label = line.strip('\n').split('\t')
                yield entity_id, label

    @staticmethod
    def entity_to_whitelist_type_iterator(type_mapping_file: str) -> Iterator[Tuple[str, str]]:
        logger.info("Yielding type mapping from %s ..." % type_mapping_file)
        with open(type_mapping_file, "r", encoding="utf8") as file:
            for line in file:
                entity_id, whitelist_type = line.strip('\n').split('\t')
                yield entity_id, whitelist_type

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
                line = line.strip()
                if line:
                    lst = line.split("\t")
                    entity_id = lst[0].strip()
                    if entity_id in adjustments["REPLACE_WITH"]:
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
    def read_wikidata_aliases() -> Dict[str, Set[str]]:
        filename = settings.QID_TO_ALIASES_FILE
        logger.info("Loading Wikidata aliases from %s ..." % filename)
        mapping = {}
        for i, line in enumerate(open(filename)):
            values = line.strip('\n').split('\t')
            entity_id = values[0]
            name = values[1]
            synonyms = {synonym for synonym in values[2].split(";") if len(synonym) > 0}
            synonyms.add(name)
            mapping[entity_id] = synonyms
        logger.info("-> %d Wikidata aliases loaded." % len(mapping))
        return mapping

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
    def read_names() -> Iterator[Tuple[str, str]]:
        filename = settings.QID_TO_NAME_FILE
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
    def get_sitelink_counts(min_count: Optional[int] = 1) -> Dict[str, int]:
        filename = settings.QID_TO_SITELINK_FILE
        logger.info("Loading sitelink counts >= %d from %s ..." % (min_count, filename))
        counts = {}
        with open(filename) as f:
            for line in f:
                entity_id, count = line.strip('\n').split('\t')
                count = int(count)
                if count >= min_count:
                    counts[entity_id] = count
        logger.info("-> %d sitelink counts loaded." % len(counts))
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
        with open(filename) as f:
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
    def read_into_set(file):
        new_set = set()
        with open(file) as f:
            for line in f:
                item = line.strip('\n')
                new_set.add(item)
        return new_set
