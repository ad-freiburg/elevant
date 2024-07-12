from typing import Optional

from elevant.evaluation.groundtruth_label import GroundtruthLabel


class WikidataEntity:
    def __init__(self,
                 entity_id: str,
                 name: str,
                 type: Optional[str] = GroundtruthLabel.OTHER):
        self.name = name
        self.entity_id = entity_id
        self.type = type

    def __lt__(self, other) -> bool:
        return self.entity_id < other.entity_id
