from typing import Dict, Tuple, Set, Optional

from spacy.tokens import Doc
from spacy.language import Language

from src.abstract_entity_linker import AbstractEntityLinker
from src.entity_linker_loader import EntityLinkerLoader
from src.entity_prediction import EntityPrediction
from src.settings import NER_IGNORE_TAGS


class TrainedEntityLinker(AbstractEntityLinker):
    LINKER_IDENTIFIER = "LINKER"

    def __init__(self,
                 name: Optional[str] = None,
                 model: Optional[Language] = None):
        if model is None:
            self.model = EntityLinkerLoader.load_trained_linker(name)
        else:
            self.model = model
            self.model.add_pipe(EntityLinkerLoader.load_entity_linker(name))
        self.kb = self.model.get_pipe("entity_linker").kb
        self.known_entities = set(self.kb.get_entity_strings())

    def predict(self,
                text: str,
                doc: Optional[Doc] = None) -> Dict[Tuple[int, int], EntityPrediction]:
        if doc is None:
            doc = self.model(text)
        predictions = {}
        for ent in doc.ents:
            if ent.label_ in NER_IGNORE_TAGS:
                continue
            span = (ent.start_char, ent.end_char)
            entity_id = ent.kb_id_ if ent.kb_id_ != "NIL" else None
            candidates = self.get_candidates(text[span[0]:span[1]])
            predictions[span] = EntityPrediction(span, entity_id, candidates)
        return predictions

    def get_candidates(self, snippet: str) -> Set[str]:
        return {candidate.entity_ for candidate in self.kb.get_candidates(snippet)}

    def contains_entity(self, entity_id):
        return entity_id in self.known_entities
