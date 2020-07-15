from typing import Iterator, Set

from src.wikidata_entity import WikidataEntity


class EntityDatabase:
    def __init__(self):
        self.entities = {}
        self.aliases = {}
        self.wikipedia2wikidata = {}
        self.wikidata2wikipedia = {}

    def add_alias(self, alias: str, entity_id: str):
        if alias not in self.aliases:
            self.aliases[alias] = {entity_id}
        else:
            self.aliases[alias].add(entity_id)

    def add_entity(self, entity: WikidataEntity):
        self.entities[entity.entity_id] = entity
        for alias in [entity.name] + entity.synonyms:
            self.add_alias(alias, entity.entity_id)

    def contains(self, entity_id):
        return entity_id in self.entities

    def get(self, entity_id) -> WikidataEntity:
        return self.entities[entity_id]

    def get_score(self, entity_id) -> int:
        return self.get(entity_id).score

    def size_entities(self) -> int:
        return len(self.entities)

    def size_aliases(self) -> int:
        return len(self.aliases)

    def all_entities(self) -> Iterator[WikidataEntity]:
        for entity_id in self.entities:
            yield self.entities[entity_id]

    def all_aliases(self) -> Iterator[str]:
        for alias in self.aliases:
            yield alias

    def contains_alias(self, alias: str):
        return alias in self.aliases

    def get_candidates(self, alias: str) -> Set[str]:
        if alias in self.aliases:
            return self.aliases[alias]
        else:
            return set()

    def add_mapping(self, wikipedia_url: str, wikidata_id: str):
        self.wikipedia2wikidata[wikipedia_url] = wikidata_id
        self.wikidata2wikipedia[wikidata_id] = wikipedia_url
