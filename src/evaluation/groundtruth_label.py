from typing import Tuple, Optional, List, Dict


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
                 coref: Optional[bool] = None,
                 desc: Optional[bool] = False):
        self.id = label_id
        self.span = span
        self.entity_id = entity_id
        self.name = name  # Needed so the web app can display the entity name
        self.optional = optional
        self.parent = parent
        self.children = children if children is not None else []
        self.type = type
        self.coref = coref
        self.desc = desc

    def is_optional(self) -> bool:
        return self.optional or self.is_quantity() or self.is_datetime() or self.desc

    def is_quantity(self) -> bool:
        return self.QUANTITY in self.get_types()

    def is_datetime(self) -> bool:
        return self.DATETIME in self.get_types()

    def is_coref(self) -> Optional[bool]:
        # self.coref is only True or False if the coref property was explicitly set in the ground truth.
        # Otherwise it is None.
        return self.coref

    def get_types(self) -> List[str]:
        return self.type.split("|")

    def to_dict(self) -> Dict:
        d = {"id": self.id,
             "span": self.span,
             "entity_id": self.entity_id,
             "name": self.name,
             "type": self.type}
        if self.parent is not None:
            d["parent"] = self.parent
        if len(self.children) > 0:
            d["children"] = self.children
        if self.optional:
            d["optional"] = self.optional
        if self.desc:
            d["desc"] = self.desc
        if self.coref is not None:
            d["coref"] = self.coref
        return d

    def __lt__(self, other):
        return self.id < other.id

    def has_non_optional_child(self, label_dict):
        """
        Recursively determine whether the ground truth label has non-optional
        children.
        """
        has_non_optional_children = False
        for child_id in self.children:
            # Determine whether there are non-optional direct children of the current label
            child_gt_label = label_dict[child_id]
            if not child_gt_label.is_optional():
                return True
            # Recursively determine whether there are non-optional indirect children of the
            # current label
            has_non_optional_children = child_gt_label.has_non_optional_child(label_dict)
            if has_non_optional_children:
                return True
        return has_non_optional_children


def groundtruth_label_from_dict(data: Dict) -> GroundtruthLabel:
    return GroundtruthLabel(label_id=data["id"],
                            span=tuple(data["span"]),
                            entity_id=data["entity_id"],
                            name=data["name"] if "name" in data else "",
                            parent=data["parent"] if "parent" in data else None,
                            children=data["children"] if "children" in data else None,
                            optional=data["optional"] if "optional" in data else False,
                            type=data["type"] if "type" in data else GroundtruthLabel.OTHER,
                            coref=data["coref"] if "coref" in data else None,
                            desc=data["desc"] if "desc" in data else False)
