from typing import Tuple, Optional, List, Dict


def is_level_one(entity_name):
    if entity_name != "Unknown":
        alpha_chars = [char for char in entity_name if char.isalpha()]
        # Check if first alphabetic character exists and is uppercase
        if len(alpha_chars) > 0 and alpha_chars[0].isupper():
            return True
    return False


class GroundtruthLabel:
    QUANTITY = "QUANTITY"
    DATETIME = "DATETIME"
    OTHER = "OTHER"

    def __init__(self,
                 label_id: int,
                 span: Tuple[int, int],
                 entity_id: str,
                 name: str,
                 parent: Optional[int] = None,
                 children: Optional[List[int]] = None,
                 optional: Optional[bool] = False,
                 type: Optional[str] = OTHER,
                 level1: Optional[bool] = None):
        self.id = label_id
        self.span = span
        self.entity_id = entity_id
        self.name = name  # Needed so the web app can display the entity name
        self.optional = optional
        self.parent = parent
        self.children = children if children is not None else []
        self.type = type
        self.level1 = level1

    def is_optional(self) -> bool:
        return self.optional or self.is_quantity() or self.is_datetime()

    def is_quantity(self) -> bool:
        return self.type == self.QUANTITY

    def is_datetime(self) -> bool:
        return self.type == self.DATETIME

    def is_level_one(self) -> bool:
        return self.level1

    def to_dict(self) -> Dict:
        d = {"id": self.id,
             "span": self.span,
             "entity_id": self.entity_id,
             "name": self.name,
             "parent": self.parent,
             "children": self.children,
             "optional": self.optional,
             "type": self.type,
             "level1": self.level1}
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
                            type=data["type"] if "type" in data else GroundtruthLabel.OTHER,
                            level1=data["level1"] if "level1" in data else None)
