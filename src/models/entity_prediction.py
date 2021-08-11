from typing import Tuple, Set, Dict


class EntityPrediction:
    def __init__(self,
                 span: Tuple[int, int],
                 entity_id: str,
                 candidates: Set[str]):
        self.span = span
        self.entity_id = entity_id
        self.candidates = candidates

    def to_dict(self) -> Dict:
        return {
            "span": self.span,
            "entity_id": self.entity_id,
            "candidates": tuple(self.candidates)
        }


def entity_prediction_from_dict(data: Dict) -> EntityPrediction:
    return EntityPrediction(data["span"], data["entity_id"], set(data["candidates"]))
