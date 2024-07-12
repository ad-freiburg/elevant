from typing import Tuple, Dict, Optional, Set


class EntityMention:
    def __init__(self,
                 span: Tuple[int, int],
                 recognized_by: Optional[str] = None,
                 entity_id: Optional[str] = None,
                 linked_by: Optional[str] = None,
                 candidates: Optional[Set[str]] = None,
                 referenced_span: Optional[Tuple[int, int]] = None,
                 contained: Optional[bool] = None):
        self.span = span
        self.recognized_by = recognized_by
        self.entity_id = entity_id
        self.linked_by = linked_by
        self.referenced_span = referenced_span
        self.candidates = candidates if candidates is not None else set()
        self.contained = contained

    def to_dict(self, evaluation_format: Optional[bool] = True) -> Dict:
        d = {"span": self.span}
        if self.entity_id is not None:
            d["id"] = self.entity_id
        if evaluation_format:
            if self.recognized_by is not None:
                d["recognized_by"] = self.recognized_by
            if self.linked_by is not None:
                d["linked_by"] = self.linked_by
            if self.referenced_span is not None:
                d["referenced_span"] = self.referenced_span
            if self.candidates is not None:
                d["candidates"] = sorted(self.candidates)
            if self.contained is not None:
                d["contained"] = self.contained
        return d

    def link(self, entity_id: str, linked_by: str):
        self.entity_id = entity_id
        self.linked_by = linked_by

    def overlaps(self, span: Tuple[int, int]) -> bool:
        return self.span[0] < span[1] and self.span[1] > span[0]

    def __str__(self) -> str:
        return str(self.to_dict())

    def __repr__(self) -> str:
        return str(self)

    def __lt__(self, other) -> bool:
        return tuple(self.span) < tuple(other.span)


def entity_mention_from_dict(data: Dict) -> EntityMention:
    return EntityMention(span=tuple(data["span"]),
                         recognized_by=data["recognized_by"] if "recognized_by" in data else None,
                         entity_id=data["id"] if "id" in data else None,
                         linked_by=data["linked_by"] if "linked_by" in data else None,
                         referenced_span=data["referenced_span"] if "referenced_span" in data else None,
                         candidates=set([ent_id for ent_id in data["candidates"]]) if "candidates" in data else None,
                         contained=data["contained"] if "contained" in data else None)
