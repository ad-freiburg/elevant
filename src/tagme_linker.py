from typing import Dict, Tuple

import tagme
import numpy as np

from src.entity_database import EntityDatabase
from src.entity_prediction import EntityPrediction


TAGME_TOKEN = "56af583d-5f6e-496f-aea2-eab06673b6a3-843339462"
tagme.GCUBE_TOKEN = TAGME_TOKEN


class TagMeLinker:
    NER_IDENTIFIER = "TagMe"
    LINKER_IDENTIFIER = "TagMe"

    def __init__(self, rho_threshold: float):
        self.entity_db = EntityDatabase()
        self.entity_db.load_mapping()
        self.entity_db.load_redirects()
        self.model = None
        self.rho_threshold = rho_threshold

    def predict(self, text: str, doc=None) -> Dict[Tuple[int, int], EntityPrediction]:
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
                    predictions[span] = EntityPrediction(span, qid, {qid})
        return predictions

    def has_entity(self, entity_id: str) -> bool:
        return True
