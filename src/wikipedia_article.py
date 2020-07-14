from typing import List, Dict, Tuple

import json

from src.entity_mention import EntityMention


class WikipediaArticle:
    def __init__(self,
                 id: int,
                 title: str,
                 text: str,
                 links: List[Tuple[Tuple[int, int], str]],
                 entity_mentions: List[EntityMention] = []):
        self.id = id
        self.title = title
        self.text = text
        self.links = links
        self.entity_mentions = entity_mentions

    def to_dict(self) -> Dict:
        data = {"id": self.id,
                "title": self.title,
                "text": self.text,
                "links": self.links,
                "entity_mentions": self.entity_mentions}
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def add_entity_mention(self, entity_mention: EntityMention):
        self.entity_mentions.append(entity_mention)

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
                            entity_mentions=data["entity_mentions"] if "entity_mentions" in data else [])


def article_from_json(dump: str):
    return article_from_dict(json.loads(dump))
