from typing import Tuple, Set


class EntityPrediction:
    def __init__(self,
                 span: Tuple[int, int],
                 entity_id: str,
                 candidates: Set[str]):
        self.span = span
        self.entity_id = entity_id
        self.candidates = candidates
