from typing import Optional, Dict, Tuple, Set

import pickle
import spacy
from spacy.tokens.doc import Doc

from src.abstract_entity_linker import AbstractEntityLinker
from src.entity_prediction import EntityPrediction
from src import settings
from src.link_entity_linker import get_mapping
from src.ner_postprocessing import shorten_entities


class LinkFrequencyEntityLinker(AbstractEntityLinker):
    def __init__(self, load_model: bool = True):
        if load_model:
            self.model = spacy.load(settings.LARGE_MODEL_NAME)
            self.model: spacy.language.Language
            self.model.add_pipe(shorten_entities, name="shorten_ner", after="ner")
        self.mapping = get_mapping()
        self.entity_ids = {self.mapping[url] for url in self.mapping}
        with open(settings.LINK_FREEQUENCIES_FILE, "rb") as f:
            self.link_frequencies = pickle.load(f)

    def get_candidates(self, snippet: str) -> Set[str]:
        link_targets = self.link_frequencies[snippet] if snippet in self.link_frequencies else []
        candidates = {self.mapping[target] for target in link_targets if target in self.mapping}
        return candidates

    def select_entity(self, snippet: str, candidates: Set[str]) -> Optional[str]:
        if len(candidates) == 0:
            return None
        frequencies = self.link_frequencies[snippet]
        best_frequency, best_candidate = max((frequencies[c], c) for c in candidates)
        return best_candidate

    def predict(self, text: str, doc: Optional[Doc] = None) -> Dict[Tuple[int, int], EntityPrediction]:
        if doc is None:
            doc = self.model(text)
        predictions = {}
        for ent in doc.ents:
            ent: spacy.tokens.Span
            candidates = self.get_candidates(ent.text)
            entity_id = self.select_entity(ent.text, candidates)
            span = (ent.start_char, ent.end_char)
            predictions[span] = EntityPrediction(span, entity_id, candidates)
        return predictions

    def has_entity(self, entity_id: str) -> bool:
        return entity_id in self.entity_ids
