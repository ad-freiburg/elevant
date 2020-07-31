from typing import List, Dict, Tuple, Optional

import json
import numpy as np

from src.entity_mention import EntityMention, entity_mention_from_dict


class WikipediaArticle:
    def __init__(self,
                 id: int,
                 title: str,
                 text: str,
                 links: List[Tuple[Tuple[int, int], str]],
                 url: Optional[str] = None,
                 entity_mentions: Optional[List[EntityMention]] = None,
                 evaluation_span: Optional[Tuple[int, int]] = None,
                 labels: Optional[List[Tuple[Tuple[int, int], str]]] = None):
        self.id = id
        self.title = title
        self.text = text
        self.links = links
        self.url = url
        self.entity_mentions = None
        self.entity_coverage = None
        self.add_entity_mentions(entity_mentions)
        self.evaluation_span = evaluation_span
        self.labels = labels

    def to_dict(self) -> Dict:
        data = {"id": self.id,
                "title": self.title,
                "text": self.text,
                "links": self.links}
        if self.url is not None:
            data["url"] = self.url
        if self.entity_mentions is not None:
            data["entity_mentions"] = [self.entity_mentions[span].to_dict() for span in sorted(self.entity_mentions)]
        if self.evaluation_span is not None:
            data["evaluation_span"] = self.evaluation_span
        if self.labels is not None:
            data["labels"] = self.labels
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def add_entity_mentions(self, entity_mentions: Optional[List[EntityMention]]):
        if self.entity_mentions is None and entity_mentions is not None:
            self.entity_mentions = {}
        if entity_mentions is not None:
            for entity_mention in entity_mentions:
                self.entity_mentions[entity_mention.span] = entity_mention
        self._update_entity_coverage()

    def _update_entity_coverage(self):
        self.entity_coverage = np.zeros(len(self.text), dtype=bool)
        if self.entity_mentions is not None:
            for span in self.entity_mentions:
                begin, end = span
                self.entity_coverage[begin:end] = True

    def overlaps_entity_mention(self, span: Tuple[int, int]) -> bool:
        begin, end = span
        return np.sum(self.entity_coverage[begin:end]) > 0

    def is_entity_mention(self, span: Tuple[int, int]) -> bool:
        return self.entity_mentions is not None and span in self.entity_mentions

    def get_entity_mention(self, span: Tuple[int, int]) -> EntityMention:
        return self.entity_mentions[span]

    def set_evaluation_span(self, start: int, end: int):
        self.evaluation_span = (start, end)

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return str(self)


def article_from_dict(data: Dict):
    links = [(tuple(span), target) for span, target in data["links"]]  # span is saved as list, but must be tuple
    return WikipediaArticle(id=int(data["id"]),
                            title=data["title"],
                            text=data["text"],
                            links=links,
                            url=data["url"] if "url" in data else None,
                            entity_mentions=[entity_mention_from_dict(entity_mention_dict) for entity_mention_dict in
                                             data["entity_mentions"]] if "entity_mentions" in data else None,
                            evaluation_span=data["evaluation_span"] if "evaluation_span" in data else None,
                            labels=data["labels"] if "labels" in data else None)


def article_from_json(dump: str):
    return article_from_dict(json.loads(dump))
