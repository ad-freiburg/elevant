from typing import List


class WikidataEntity:
    def __init__(self,
                 name: str,
                 score: int,
                 entity_id: str,
                 synonyms: List[str]):
        self.name = name
        self.score = score
        self.entity_id = entity_id
        self.synonyms = synonyms

    def __lt__(self, other):
        return self.entity_id < other.entity_id
