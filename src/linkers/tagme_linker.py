from typing import Dict, Tuple, Optional

import tagme
import numpy as np

from src.models.entity_database import EntityDatabase
from src.models.entity_prediction import EntityPrediction
from src.linkers.abstract_entity_linker import AbstractEntityLinker


tagme.GCUBE_TOKEN = "56af583d-5f6e-496f-aea2-eab06673b6a3-843339462"


class TagMeLinker(AbstractEntityLinker):
    NER_IDENTIFIER = LINKER_IDENTIFIER = "TAGME"

    def __init__(self, rho_threshold: float = 0.2):
        self.entity_db = EntityDatabase()
        self.entity_db.load_mapping()
        self.entity_db.load_redirects()
        self.model = None
        self.rho_threshold = rho_threshold

    def predict(self,
                text: str,
                doc=None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
        annotations = tagme.annotate(text).get_annotations(self.rho_threshold)
        annotations = sorted(annotations, key=lambda ann: ann.score, reverse=True)
        predictions = {}
        annotated_chars = np.zeros(shape=len(text), dtype=bool)
        for ann in annotations:
            qid = self.entity_db.link2id(ann.entity_title)
            if qid is not None:
                if np.sum(annotated_chars[ann.begin:ann.end]) == 0:
                    annotated_chars[ann.begin:ann.end] = True
                    span = (ann.begin, ann.end)
                    snippet = text[span[0]:span[1]]
                    if uppercase and snippet.islower():
                        continue
                    predictions[span] = EntityPrediction(span, qid, {qid})
        return predictions

    def has_entity(self, entity_id: str) -> bool:
        return True
