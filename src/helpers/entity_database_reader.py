from typing import List, Iterator, Tuple, Dict, Set, Optional

from urllib.parse import unquote
import pickle

from src import settings
from src.evaluation.groundtruth_label import GroundtruthLabel
from src.models.gender import Gender
from src.models.wikidata_entity import WikidataEntity


WIKI_URL_PREFIX = "https://en.wikipedia.org/wiki/"


class EntityDatabaseReader:
    @staticmethod
    def read_entity_file() -> List[WikidataEntity]:
        return EntityDatabaseReader._read_entity_file(settings.WIKIDATA_ENTITIES_FILE)

    @staticmethod
    def _read_entity_file(path: str) -> List[WikidataEntity]:
        entities = []
        for i, line in enumerate(open(path)):
            values = line.strip('\n').split('\t')
            name = values[0]
            score = int(values[1])
            entity_id = values[2]
            synonyms = [synonym for synonym in values[3].split(";") if len(synonym) > 0]
            entity = WikidataEntity(name, score, entity_id, synonyms)
            entities.append(entity)
        return entities

    @staticmethod
    def read_entity_database() -> Dict[str, WikidataEntity]:
        entities = dict()
        for i, line in enumerate(open(settings.WIKIDATA_ENTITIES_FILE)):
            values = line.strip('\n').split('\t')
            name = values[0]
            score = int(values[1])
            entity_id = values[2]
            synonyms = [synonym for synonym in values[3].split(";") if len(synonym) > 0]
            entity = WikidataEntity(name, score, entity_id, synonyms)
            entities[entity_id] = entity
        return entities

    @staticmethod
    def get_link_frequencies() -> Dict[str, Dict[str, int]]:
        with open(settings.LINK_FREEQUENCIES_FILE, "rb") as f:
            link_frequencies = pickle.load(f)
        return link_frequencies

    @staticmethod
    def get_link_redirects() -> Dict[str, str]:
        with open(settings.REDIRECTS_FILE, "rb") as f:
            redirects = pickle.load(f)
        return redirects

    @staticmethod
    def get_title_synonyms() -> Dict[str, Set[str]]:
        with open(settings.TITLE_SYNONYMS_FILE, "rb") as f:
            title_synonyms = pickle.load(f)
        return title_synonyms

    @staticmethod
    def get_akronyms() -> Dict[str, Set[str]]:
        with open(settings.AKRONYMS_FILE, "rb") as f:
            akronyms = pickle.load(f)
        return akronyms

    @staticmethod
    def get_wikipedia_to_wikidata_mapping(mappings_file: str = settings.QID_TO_WIKIPEDIA_URL_FILE):
        mapping = {}
        for i, line in enumerate(open(mappings_file)):
            entity_id, link_url = line.strip('\n').split('\t')
            link_url = unquote(link_url)
            entity_name = link_url[len(WIKI_URL_PREFIX):].replace('_', ' ')
            mapping[entity_name] = entity_id
        return mapping

    @staticmethod
    def get_wikidata_entities_with_types(relevant_entities: Set[str], type_mapping_file: str) -> Dict[str, WikidataEntity]:
        entities = dict()
        id_to_type = dict()
        for entity_id, whitelist_type in EntityDatabaseReader.entity_to_whitelist_type_iterator(type_mapping_file):
            if entity_id in relevant_entities:
                if entity_id not in id_to_type:  # An entity can have multiple types from the whitelist
                    id_to_type[entity_id] = []
                id_to_type[entity_id].append(whitelist_type)

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
            entity = WikidataEntity(name, 0, entity_id, [], type=types)
            entities[entity_id] = entity
        return entities

    @staticmethod
    def entity_to_label_iterator() -> Iterator[Tuple[str, str]]:
        with open(settings.QID_TO_LABEL_FILE, "r", encoding="utf8") as file:
            for line in file:
                entity_id, label = line.strip('\n').split('\t')
                yield entity_id, label

    @staticmethod
    def entity_to_whitelist_type_iterator(type_mapping_file: str) \
            -> Iterator[Tuple[str, str]]:
        with open(type_mapping_file, "r", encoding="utf8") as file:
            for line in file:
                lst = line.strip().split()
                entity_id = lst[0][3:]
                whitelist_type = lst[1][3:]
                yield entity_id, whitelist_type

    @staticmethod
    def read_whitelist_types(whitelist_file: Optional[str] = settings.WHITELIST_FILE) -> Dict[str, str]:
        types = dict()
        with open(whitelist_file, "r", encoding="utf8") as file:
            for line in file:
                line = line.strip()
                if line:
                    lst = line.split("#")
                    entity_id = lst[0].strip()[3:]
                    name = lst[1].strip()
                    types[entity_id] = name
        return types

    @staticmethod
    def get_gender_mapping(mappings_file: str = settings.QID_TO_GENDER_FILE) -> Dict[str, Gender]:
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
        return mapping

    @staticmethod
    def read_names() -> Iterator[Tuple[str, str]]:
        for line in open(settings.QID_TO_GIVEN_NAME_FILE):
            entity_id, name = line.strip('\n').split('\t')
            yield entity_id, name

    @staticmethod
    def get_type_mapping(mappings_file: str = settings.QID_TO_RELEVANT_TYPES_FILE) -> Dict[str, List[str]]:
        mapping = {}
        for i, line in enumerate(open(mappings_file)):
            line = line[:-1]
            entity_id, types = line.split("\t")
            mapping[entity_id] = types.split(";")
        return mapping

    @staticmethod
    def get_unigram_counts() -> Dict[str, int]:
        counts = {}
        with open(settings.UNIGRAMS_FILE) as f:
            for line in f:
                unigram, count = line.split()
                counts[unigram] = int(count)
        return counts

    @staticmethod
    def get_sitelink_counts(min_count: Optional[int] = 1) -> Dict[str, int]:
        counts = {}
        with open(settings.QID_TO_SITELINK_FILE) as f:
            for line in f:
                entity_id, count = line.strip('\n').split('\t')
                count = int(count)
                if count >= min_count:
                    counts[entity_id] = count
        return counts

    @staticmethod
    def get_demonyms() -> Dict[str, List[str]]:
        demonyms = {}
        with open(settings.QID_TO_DEMONYM_FILE) as f:
            for line in f:
                entity_id, demonym = line.strip('\n').split('\t')
                if demonym not in demonyms:
                    demonyms[demonym] = []
                if demonym + "s" not in demonyms:
                    demonyms[demonym + "s"] = []
                demonyms[demonym].append(entity_id)
                demonyms[demonym + "s"].append(entity_id)
        return demonyms

    @staticmethod
    def get_languages() -> Dict[str, str]:
        languages = {}
        with open(settings.QID_TO_LANGUAGE_FILE) as f:
            for line in f:
                entity_id, language = line.strip('\n').split('\t')
                languages[language] = entity_id
        return languages

    @staticmethod
    def get_real_numbers() -> Set[str]:
        return EntityDatabaseReader.read_into_set(settings.QUANTITY_FILE)

    @staticmethod
    def get_points_in_time() -> Set[str]:
        return EntityDatabaseReader.read_into_set(settings.DATETIME_FILE)

    @staticmethod
    def get_wikipedia_id2wikipedia_title_mapping() -> Dict[int, str]:
        wikipedia_id2_wikipedia_title = dict()
        with open(settings.WIKIPEDIA_ID_TO_TITLE_FILE) as f:
            for line in f:
                wikipedia_id, title = line.strip('\n').split("\t")
                wikipedia_id = int(wikipedia_id)
                wikipedia_id2_wikipedia_title[wikipedia_id] = title
        return wikipedia_id2_wikipedia_title

    @staticmethod
    def get_instance_of_mapping(relevant_entities=None):
        return EntityDatabaseReader.read_item_to_qid_set_mapping(settings.QID_TO_INSTANCE_OF_FILE, relevant_entities)

    @staticmethod
    def get_subclass_of_mapping(relevant_entities=None):
        return EntityDatabaseReader.read_item_to_qid_set_mapping(settings.QID_TO_SUBCLASS_OF_FILE, relevant_entities)

    @staticmethod
    def get_coarse_types():
        return EntityDatabaseReader.read_into_set(settings.COARSE_TYPES)

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
