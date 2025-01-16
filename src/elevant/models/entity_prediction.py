from typing import Tuple, Set, Dict, Optional


class EntityPrediction:
    def __init__(self,
                 span: Tuple[int, int],
                 entity_id: str,
                 candidates: Set[str],
                 score: Optional[float] = None):
        self.span = span
        self.entity_id = entity_id
        self.candidates = candidates
        self.score = score

    def to_dict(self) -> Dict:
        d = {
            "span": self.span,
            "entity_id": self.entity_id,
            "candidates": tuple(self.candidates)
        }
        if self.score is not None:
            d["score"] = self.score
        return d


def entity_prediction_from_dict(data: Dict) -> EntityPrediction:
    score = data["score"] if "score" in data else None
    return EntityPrediction(data["span"], data["entity_id"], set(data["candidates"]), score)
