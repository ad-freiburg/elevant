from typing import List

from src.entity_database import EntityDatabase
from src.wikidata_entity import WikidataEntity
from src import settings


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
    def read_entity_database(minimum_score: int = 0,
                             verbose: bool = True) -> EntityDatabase:
        entity_db = EntityDatabase()
        if verbose:
            print("reading entities...")
        for entity in EntityDatabaseReader._read_entity_file(settings.ENTITY_FILE):
            entity_id = entity.entity_id
            if entity.score >= minimum_score and \
                    (not entity_db.contains(entity_id) or entity.score > entity_db.get_score(entity_id)):
                entity_db.add_entity(entity)
        if verbose:
            print(entity_db.size_entities(), "entities")
            print(entity_db.size_aliases(), "aliases")
            print("reading person names...")
        EntityDatabaseReader._add_names(entity_db, settings.PERSON_NAMES_FILE)
        if verbose:
            print(entity_db.size_aliases(), "aliases")
        return entity_db

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
    def _add_names(entity_db: EntityDatabase, names_file: str):
        for line in open(names_file):
            wikidata_url, encoded_names = line[:-1].split(">,")
            entity_id = parse_entity_id(wikidata_url)
            if entity_db.contains(entity_id):
                entity_names = [parse_name(encoded) for encoded in encoded_names.split("@en,")]
                for name in entity_names:
                    entity_db.add_alias(name, entity_id)
