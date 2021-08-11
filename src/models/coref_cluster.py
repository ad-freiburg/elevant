from typing import Optional, Tuple, List


class CorefCluster:
    def __init__(self, main: Tuple[int, int], mentions: List[Tuple[int, int]], entity_id: Optional[str] = None):
        self.main = main
        self.mentions = mentions
        self.entity_id = entity_id
