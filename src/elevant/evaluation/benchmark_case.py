import json
from enum import Enum
from typing import Dict


class BenchmarkCaseLabel(Enum):
    CAPITALIZED = "CAPITALIZED"
    LOWERCASED = "LOWERCASED"
    NON_ALPHA = "NON_ALPHA"
    LOWERCASED_NON_NAMED = "LOWERCASED_NON_NAMED"
    DEMONYM = "DEMONYM"
    METONYM = "METONYM"
    PARTIAL_NAME = "PARTIAL_NAME"
    RARE = "RARE"
    UNKNOWN = "UNKNOWN"
    UNKNOWN_NIL = "UNKNOWN_NIL"
    UNKNOWN_NO_MAPPING = "UNKNOWN_NO_MAPPING"
    OPTIONAL = "OPTIONAL"
    ROOT = "ROOT"
    CHILD = "CHILD"


class BenchmarkCase:
    def __init__(self, span, groundtruth_label):
        self.span = span
        self.groundtruth_label = groundtruth_label
        self.tags = set()
        self.types = set()
        self.mention_type = None
        self.mention_word_count = None

    def add_tag(self, tag):
        self.tags.add(tag)

    def set_types(self, types):
        self.types = types

    def set_mention_type(self, mention_type):
        self.mention_type = mention_type

    def set_mention_word_count(self, num_words):
        self.mention_word_count = num_words

    def to_dict(self) -> Dict:
        data = {"span": self.span,
                "groundtruth_label": self.groundtruth_label.to_dict(),
                "tags": sorted([tag.value for tag in self.tags]),
                "types": sorted(self.types),
                "mention_type": self.mention_type.value,
                "mention_word_count": self.mention_word_count}
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
