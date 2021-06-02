from enum import Enum
from typing import Tuple, Optional, List, Dict


class EntityType(Enum):
    OTHER = "OTHER"
    QUANTITY = "QUANTITY"
    DATETIME = "DATETIME"


class GroundtruthLabel:
    def __init__(self,
                 label_id: int,
                 span: Tuple[int, int],
                 entity_id: str,
                 name: str,
                 parent: int = None,
                 children: Optional[List[int]] = None,
                 optional: Optional[bool] = False,
                 type: Optional[EntityType] = EntityType.OTHER):
        self.id = label_id
        self.span = span
        self.entity_id = entity_id
        self.name = name  # Needed so the web app can display the entity name
        self.optional = optional
        self.parent = parent
        self.children = children if children is not None else []
        self.type = type

    def is_optional(self) -> bool:
        return self.optional or self.type in (EntityType.QUANTITY, EntityType.DATETIME)

    def to_dict(self) -> Dict:
        d = {"id": self.id,
             "span": self.span,
             "entity_id": self.entity_id,
             "name": self.name,
             "parent": self.parent,
             "children": self.children,
             "optional": self.optional,
             "type": self.type.value}
        return d

    def __lt__(self, other):
        return self.id < other.id


def groundtruth_label_from_dict(data: Dict) -> GroundtruthLabel:
    return GroundtruthLabel(label_id=data["id"],
                            span=tuple(data["span"]),
                            entity_id=data["entity_id"],
                            name=data["name"] if "name" in data else "",
                            parent=data["parent"] if "parent" in data else None,
                            children=data["children"] if "children" in data else None,
                            optional=data["optional"] if "optional" in data else False,
                            type=EntityType(data["type"]) if "type" in data else None)
