from typing import Optional, List, Tuple, Dict

import json
import numpy as np

from src.entity_mention import EntityMention, entity_mention_from_dict


class Paragraph:
    def __init__(self,
                 text: str,
                 wikipedia_links: Optional[List[Tuple[Tuple[int, int], str]]] = None,
                 entity_mentions: Optional[List[EntityMention]] = None):
        self.text = text
        self.wikipedia_links = wikipedia_links
        self.entity_mentions = entity_mentions
        self.entity_coverage = np.full(len(text), False)
        if entity_mentions is not None:
            self._update_entity_coverage(self.entity_mentions)
            self.entity_mention_dict = {mention.span: mention for mention in entity_mentions}

    def to_dict(self):
        d = {"text": self.text}
        if self.wikipedia_links is not None:
            d["links"] = self.wikipedia_links
        if self.entity_mentions is not None:
            d["entities"] = [entity.to_dict() for entity in self.entity_mentions]
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def remove_entity_mentions(self):
        if self.entity_mentions is not None:
            self.entity_mentions = None
            self.entity_coverage = np.full(len(self.text), False)

    def add_entity_mentions(self, entity_mentions: List[EntityMention]):
        if self.entity_mentions is None:
            self.entity_mentions = []
            self.entity_mention_dict = {}
        self.entity_mentions = sorted(self.entity_mentions + entity_mentions)
        self._update_entity_coverage(entity_mentions)
        for mention in entity_mentions:
            self.entity_mention_dict[mention.span] = mention

    def overlaps_entity(self, span: Tuple[int, int]):
        begin, end = span
        return np.sum(self.entity_coverage[begin:end]) > 0

    def _update_entity_coverage(self, entity_mentions: List[EntityMention]):
        for mention in entity_mentions:
            begin, end = mention.span
            self.entity_coverage[begin:end] = True

    def is_entity_mention(self, span: Tuple[int, int]) -> bool:
        return span in self.entity_mention_dict

    def get_entity_mention(self, span: Tuple[int, int]) -> EntityMention:
        return self.entity_mention_dict[span]

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return str(self)


def paragraph_from_dict(data: Dict):
    if "links" in data:
        links = [(tuple(span), target) for span, target in data["links"]]
    else:
        links = None
    return Paragraph(text=data["text"],
                     wikipedia_links=links,
                     entity_mentions=[entity_mention_from_dict(entity) for entity in data["entities"]]
                     if "entities" in data else None)


def paragraph_from_json(dump: str) -> Paragraph:
    return paragraph_from_dict(json.loads(dump))
