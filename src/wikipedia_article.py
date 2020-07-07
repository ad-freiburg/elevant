from typing import Optional, List, Dict

import json

from src.paragraph import Paragraph, paragraph_from_dict


class WikipediaArticle:
    def __init__(self,
                 id: int,
                 title: str,
                 text: Optional[str] = None,
                 paragraphs: Optional[List[Paragraph]] = None):
        self.id = id
        self.title = title
        self.text = text
        self.paragraphs = paragraphs

    def to_dict(self) -> Dict:
        data = {"id": self.id,
                "title": self.title}
        if self.paragraphs is None:
            data["text"] = self.text
        else:
            data["paragraphs"] = [paragraph.to_dict() for paragraph in self.paragraphs]
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return str(self)


def article_from_dict(data: Dict):
    return WikipediaArticle(id=int(data["id"]),
                            title=data["title"],
                            text=data["text"] if "text" in data else None,
                            paragraphs=[paragraph_from_dict(paragraph_data) for paragraph_data in data["paragraphs"]]
                            if "paragraphs" in data else None)


def article_from_json(dump: str):
    return article_from_dict(json.loads(dump))
