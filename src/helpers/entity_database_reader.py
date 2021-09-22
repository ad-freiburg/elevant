from typing import List, Iterator, Tuple, Dict, Set, Optional

from urllib.parse import unquote
import pickle

from src import settings
from src.evaluation.groundtruth_label import GroundtruthLabel
from src.models.gender import Gender
from src.models.wikidata_entity import WikidataEntity


WIKI_URL_PREFIX = "https://en.wikipedia.org/wiki/"
ENTITY_PREFIX = "http://www.wikidata.org/entity/"
LABEL_SUFFIX = "@en"


def parse_entity_id(url: str) -> str:
    if url.startswith("<"):
        url = url[1:]
    if url.endswith(">"):
        url = url[:-1]
    if url.startswith(settings.ENTITY_PREFIX):
        entity_id = url[len(settings.ENTITY_PREFIX):]
    else:
        entity_id = url
    return entity_id


def parse_name(encoded_name: str) -> str:
    if '\"' not in encoded_name:
        return encoded_name
    return encoded_name.split('\"')[1]


class EntityDatabaseReader:
    @staticmethod
    def read_entity_file() -> List[WikidataEntity]:
        return EntityDatabaseReader._read_entity_file(settings.ENTITY_FILE)

    @staticmethod
    def _read_entity_file(path: str) -> List[WikidataEntity]:
        entities = []
        for i, line in enumerate(open(path)):
            if i > 0:
                values = line[:-1].split('\t')
                name = values[0]
                score = int(values[1])
                entity_id = values[4]
                synonyms = [synonym for synonym in values[5].split(";") if len(synonym) > 0]
                entity = WikidataEntity(name, score, entity_id, synonyms)
                entities.append(entity)
        return entities

    @staticmethod
    def read_entity_database() -> Dict[str, WikidataEntity]:
        entities = dict()
        for i, line in enumerate(open(settings.ENTITY_FILE)):
            if i > 0:
                values = line[:-1].split('\t')
                name = values[0]
                score = int(values[1])
                entity_id = values[4]
                synonyms = [synonym for synonym in values[5].split(";") if len(synonym) > 0]
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
    def get_mapping(mappings_file: str = settings.WIKI_MAPPING_FILE):
        mapping = {}
        for i, line in enumerate(open(mappings_file)):
            line = line[:-1]
            link_url, entity_url = line.split(">,<")
            link_url = link_url[1:]
            entity_url = entity_url[:-1]
            link_url = unquote(link_url)
            entity_name = link_url[len(WIKI_URL_PREFIX):].replace('_', ' ')
            entity_id = entity_url[len(ENTITY_PREFIX):]
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
        with open(settings.LABEL_MAPPING, "r", encoding="utf8") as file:
            for line in file:
                lst = line.strip().split("\t")
                entity_id = lst[0][:-1].split("/")[-1]
                name = lst[1][1:-4]
                yield entity_id, name

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
    def get_gender_mapping(mappings_file: str = settings.GENDER_MAPPING_FILE) -> Dict[str, Gender]:
        mapping = {}
        for i, line in enumerate(open(mappings_file)):
            line = line[:-1]
            entity_url, gender_label = line.split("\t")
            entity_url = entity_url.strip("<>")
            entity_id = entity_url[len(ENTITY_PREFIX):]
            gender_tokens = gender_label[:-len(LABEL_SUFFIX)].strip('"').split()
            if "female" in gender_tokens:
                mapping[entity_id] = Gender.FEMALE
            elif "male" in gender_tokens:
                mapping[entity_id] = Gender.MALE
            else:
                mapping[entity_id] = Gender.OTHER
        return mapping

    @staticmethod
    def read_names() -> Iterator[Tuple[str, str]]:
        for line in open(settings.GIVEN_NAME_FILE):
            wikidata_url, encoded_given_name = line[:-1].split(">\t")
            entity_id = parse_entity_id(wikidata_url)
            given_name = encoded_given_name[:-len(LABEL_SUFFIX)].strip('"')
            yield entity_id, given_name

    @staticmethod
    def get_type_mapping(mappings_file: str = settings.RELEVANT_TYPES_FILE) -> Dict[str, List[str]]:
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
    def get_sitelink_counts() -> Dict[str, int]:
        counts = {}
        with open(settings.WIKIDATA_SITELINK_COUNTS_FILE) as f:
            for line in f:
                entity_id, count = line.split()
                count = int(count)
                if count > 0:
                    counts[entity_id] = count
        return counts

    @staticmethod
    def get_demonyms() -> Dict[str, List[str]]:
        demonyms = {}
        with open(settings.DEMONYM_FILE) as f:
            for line in f:
                entity_id, demonym = line.split("\t")
                entity_id = entity_id[:-1].split("/")[-1]
                demonym = demonym.split("\"")[1]
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
        with open(settings.LANGUAGE_FILE) as f:
            for line in f:
                entity_id, language = line.split("\t")
                entity_id = entity_id[:-1].split("/")[-1]
                language = language.split("\"")[1]
                languages[language] = entity_id
        return languages

    @staticmethod
    def get_real_numbers() -> Set[str]:
        real_numbers = set()
        with open(settings.REAL_NUMBERS) as f:
            for line in f:
                entity_id = line.strip()
                entity_id = entity_id[:-1].split("/")[-1]
                real_numbers.add(entity_id)
        return real_numbers

    @staticmethod
    def get_points_in_time() -> Set[str]:
        points_in_time = set()
        with open(settings.POINTS_IN_TIME) as f:
            for line in f:
                entity_id = line.strip()
                entity_id = entity_id[:-1].split("/")[-1]
                points_in_time.add(entity_id)
        return points_in_time

    @staticmethod
    def get_wikipedia_id2wikipedia_title_mapping() -> Dict[int, str]:
        wikipedia_id2_wikipedia_title = dict()
        with open(settings.WIKIPEDIA_ID_TO_TITLE_FILE) as f:
            for line in f:
                wikipedia_id, title = line.strip().split("\t")
                wikipedia_id = int(wikipedia_id)
                wikipedia_id2_wikipedia_title[wikipedia_id] = title
        return wikipedia_id2_wikipedia_title
