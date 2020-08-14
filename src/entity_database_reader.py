from typing import List, Iterator, Tuple, Dict

from urllib.parse import unquote
import pickle

from src import settings
from src.gender import Gender
from src.wikidata_entity import WikidataEntity


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
    def read_names() -> Iterator[Tuple[str, List[str]]]:
        for line in open(settings.PERSON_NAMES_FILE):
            wikidata_url, encoded_names = line[:-1].split(">,")
            entity_id = parse_entity_id(wikidata_url)
            entity_names = [parse_name(encoded) for encoded in encoded_names.split("@en,")]
            yield entity_id, entity_names

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
    def get_gender_mapping(mappings_file: str = settings.GENDER_MAPPING_FILE):
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
