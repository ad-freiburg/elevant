from typing import Dict, Tuple, Set, Optional, Any

from spacy.tokens import Doc

from elevant.linkers.abstract_entity_linker import AbstractEntityLinker
from elevant.helpers.entity_linker_loader import EntityLinkerLoader
from elevant.models.entity_prediction import EntityPrediction
from elevant.settings import NER_IGNORE_TAGS
from elevant.utils.dates import is_date

import elevant.ner.ner_postprocessing  # import is needed so Python finds the custom factory

class SpacyLinker(AbstractEntityLinker):
    def __init__(self, config: Dict[str, Any]):

        # Get config variables
        self.linker_identifier = config["linker_name"] if "linker_name" in config else "Spacy"
        self.ner_identifier = "EnhancedSpacy"
        model_name = config["model_name"] if "model_name" in config else "wikipedia"
        kb_name = config["kb"] if "kb" in config else "wikipedia"

        self.model = EntityLinkerLoader.load_trained_linker(model_name, kb_name=kb_name)
        if not self.model.has_pipe("ner_postprocessor"):
            self.model.add_pipe("ner_postprocessor", after="ner")

        self.kb = self.model.get_pipe("entity_linker").kb
        self.known_entities = set(self.kb.get_entity_strings())

    def has_entity(self, entity_id: str) -> bool:
        return entity_id in self.known_entities

    def predict(self,
                text: str,
                doc: Optional[Doc] = None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
        if doc is None:
            doc = self.model(text)
        predictions = {}
        for ent in doc.ents:
            if ent.label_ in NER_IGNORE_TAGS:
                continue
            span = (ent.start_char, ent.end_char)
            entity_id = ent.kb_id_ if ent.kb_id_ != "NIL" else None
            snippet = text[span[0]:span[1]]
            if uppercase and snippet.islower():
                continue
            if is_date(snippet):
                continue
            candidates = self.get_candidates(snippet)
            predictions[span] = EntityPrediction(span, entity_id, candidates)
        return predictions

    def get_candidates(self, snippet: str) -> Set[str]:
        return {candidate.entity_ for candidate in self.kb.get_alias_candidates(snippet)}

    def contains_entity(self, entity_id: str) -> bool:
        return entity_id in self.known_entities
