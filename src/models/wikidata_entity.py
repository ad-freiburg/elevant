from typing import Optional, Set, List

from src.evaluation.groundtruth_label import GroundtruthLabel


class WikidataEntity:
    def __init__(self,
                 name: str,
                 score: int,
                 entity_id: str,
                 synonyms: Optional[Set[str]] = None,
                 title_synonyms: Optional[Set[str]] = None,
                 akronyms: Optional[Set[str]] = None,
                 type: Optional[str] = GroundtruthLabel.OTHER):
        self.name = name
        self.score = score
        self.entity_id = entity_id
        self.synonyms = synonyms if synonyms else set()
        self.title_synonyms = title_synonyms if title_synonyms else set()
        self.akronyms = akronyms if akronyms else set()
        self.type = type

    def __lt__(self, other) -> bool:
        return self.entity_id < other.entity_id

    def add_title_synonym(self, synonym: str):
        self.title_synonyms.add(synonym)

    def add_akronym(self, akronym: str):
        self.akronyms.add(akronym)

    def is_nil(self) -> bool:
        return self.entity_id is None

    def get_types(self) -> List[str]:
        return self.type.split("|")
