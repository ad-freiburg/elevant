from typing import Dict, Set, Tuple, Iterator, Optional
from src.wikidata_entity import WikidataEntity
from src.entity_database_reader import EntityDatabaseReader
from src.link_frequency_entity_linker import get_mapping


class EntityDatabase:
    def __init__(self):
        self.entities = {}
        self.entities: Dict[str, WikidataEntity]
        self.aliases = {}
        self.aliases: Dict[str, Set[str]]
        self.wikipedia2wikidata = {}
        self.wikipedia2wikidata: Dict[str, str]
        self.wikidata2wikipedia = {}
        self.wikidata2wikipedia: Dict[str, str]
        self.link_frequencies = {}
        self.link_frequencies: Dict[str, Tuple[str, int]]
        self.redirects = {}
        self.redirects: Dict[str, str]

    def add_entity(self, entity: WikidataEntity):
        self.entities[entity.entity_id] = entity

    def contains_entity(self, entity_id: str) -> bool:
        return entity_id in self.entities

    def get_entity(self, entity_id: str) -> WikidataEntity:
        return self.entities[entity_id]

    def get_score(self, entity_id: str) -> int:
        if not self.contains_entity(entity_id):
            return 0
        return self.get_entity(entity_id).score

    def load_entities_small(self, minimum_score: int = 0):
        for entity in EntityDatabaseReader.read_entity_file():
            if entity.score >= minimum_score:
                self.add_entity(entity)

    def load_entities_big(self):
        mapping = get_mapping()
        for entity_name in mapping:
            entity_id = mapping[entity_name]
            entity = WikidataEntity(entity_name, 0, entity_id, [])
            self.add_entity(entity)

    def size_entities(self):
        return len(self.entities)

    def add_alias(self, alias: str, entity_id: str):
        if alias not in self.aliases:
            self.aliases[alias] = {entity_id}
        else:
            self.aliases[alias].add(entity_id)

    def add_synonym_aliases(self):
        for entity in EntityDatabaseReader.read_entity_file():
            if self.contains_entity(entity.entity_id):
                for alias in entity.synonyms + [entity.name]:
                    self.add_alias(alias, entity.entity_id)

    def add_name_aliases(self):
        for entity_id, names in EntityDatabaseReader.read_names():
            if self.contains_entity(entity_id):
                for name in names:
                    self.add_alias(name, entity_id)

    def size_aliases(self):
        return len(self.aliases)

    def load_mapping(self):
        mapping = get_mapping()
        for entity_name in mapping:
            entity_id = mapping[entity_name]
            self.wikipedia2wikidata[entity_name] = entity_id
            self.wikidata2wikipedia[entity_id] = entity_name

    def load_redirects(self):
        self.redirects = EntityDatabaseReader.get_link_redirects()

    def link2id(self, link_target: str) -> Optional[str]:
        if link_target in self.wikipedia2wikidata:
            return self.wikipedia2wikidata[link_target]
        elif link_target in self.redirects and self.redirects[link_target] in self.wikipedia2wikidata:
            return self.wikipedia2wikidata[self.redirects[link_target]]
        return None

    def _iterate_link_frequencies(self) -> Iterator[Tuple[str, str, int]]:
        link_frequencies = EntityDatabaseReader.get_link_frequencies()
        for link_text in link_frequencies:
            for link_target in link_frequencies[link_text]:
                entity_id = self.link2id(link_target)
                if entity_id is not None and self.contains_entity(entity_id):
                    frequency = link_frequencies[link_text][link_target]
                    yield link_text, entity_id, frequency

    def add_link_aliases(self):
        for link_text, entity_id, frequency in self._iterate_link_frequencies():
            self.add_alias(link_text, entity_id)

    def load_link_frequencies(self):
        for link_text, entity_id, frequency in self._iterate_link_frequencies():
            if link_text not in self.link_frequencies:
                self.link_frequencies[link_text] = {}
            if entity_id not in self.link_frequencies[link_text]:
                self.link_frequencies[link_text][entity_id] = frequency
            else:
                self.link_frequencies[link_text][entity_id] += frequency

    def get_candidates(self, alias: str) -> Set[str]:
        if alias not in self.aliases:
            return set()
        else:
            return self.aliases[alias]

    def get_link_frequency(self, alias, entity_id):
        if alias not in self.link_frequencies or entity_id not in self.link_frequencies[alias]:
            return 0
        return self.link_frequencies[alias][entity_id]
