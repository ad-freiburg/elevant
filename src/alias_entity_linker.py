from typing import Dict, Tuple, Optional

import pickle
import spacy
from spacy.tokens import Doc

from src.abstract_entity_linker import AbstractEntityLinker
from src.entity_prediction import EntityPrediction
from src import settings


class AliasEntityLinker(AbstractEntityLinker):
    LINKER_IDENTIFIER = "ALIAS"

    def __init__(self, load_model: bool = True):
        if load_model:
            self.model = spacy.load(settings.LARGE_MODEL_NAME)
        with open(settings.LINK_COUNTS_FILE, "rb") as f:
            self.aliases = pickle.load(f)

    def add_alias(self, alias: str, entity_id: str, frequency: int = 1):
        if alias not in self.aliases:
            self.aliases[alias] = {}
        if entity_id not in self.aliases[alias]:
            self.aliases[alias][entity_id] = frequency
        else:
            self.aliases[alias][entity_id] += frequency

    def predict(self,
                text: str,
                doc: Optional[Doc] = None) -> Dict[Tuple[int, int], EntityPrediction]:
        if doc is None:
            doc = self.model(text)
        predictions = {}
        for ent in doc.ents:
            span = (ent.start_char, ent.end_char)
            snippet = text[span[0]:span[1]]
            if snippet in self.aliases:
                candidates = set(self.aliases[snippet])
                predicted_entity_id = max(candidates, key=lambda candidate: self.aliases[snippet][candidate])
            else:
                candidates = set()
                predicted_entity_id = None
            predictions[span] = EntityPrediction(span, predicted_entity_id, candidates)
        return predictions
