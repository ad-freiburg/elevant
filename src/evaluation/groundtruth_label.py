from typing import Tuple, Optional, List, Dict


class GroundtruthLabel:
    def __init__(self,
                 label_id: int,
                 span: Tuple[int, int],
                 entity_id: str,
                 parent: int = None,
                 children: Optional[List[int]] = None):
        self.id = label_id
        self.span = span
        self.entity_id = entity_id
        self.parent = parent
        self.children = children if children is not None else []

    def to_dict(self) -> Dict:
        d = {"id": self.id,
             "span": self.span,
             "entity_id": self.entity_id,
             "parent": self.parent,
             "children": self.children}
        return d

    def __lt__(self, other):
        return self.id < other.id


def groundtruth_label_from_dict(data: Dict) -> GroundtruthLabel:
    return GroundtruthLabel(label_id=data["id"],
                            span=tuple(data["span"]),
                            entity_id=data["entity_id"],
                            parent=data["parent"] if "parent" in data else None,
                            children=data["children"] if "children" in data else None)
