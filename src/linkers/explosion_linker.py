from typing import Optional, Dict, Tuple, Set

import spacy
from spacy.tokens.doc import Doc
from spacy.language import Language
from spacy.kb import KnowledgeBase

from src.linkers.abstract_entity_linker import AbstractEntityLinker
from src.models.entity_prediction import EntityPrediction
from src.models.entity_database import EntityDatabase
from src.ner.ner_postprocessing import NERPostprocessor
from src.utils.dates import is_date


class ExplosionEntityLinker(AbstractEntityLinker):
    LINKER_IDENTIFIER = "EXPLOSION"

    def __init__(self, model_path: str, entity_db: EntityDatabase):
        self.model = spacy.load(model_path)
        self.model: Language
        if not self.model.has_pipe("ner_postprocessor"):
            ner_postprocessor = NERPostprocessor(entity_db)
            self.model.add_pipe(ner_postprocessor, name="ner_postprocessor", after="ner")
        linker = self.model.get_pipe("entity_linker")
        self.kb = linker.kb
        self.kb: KnowledgeBase

    def predict(self, text: str,
                doc: Optional[Doc] = None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
        doc = self.model(text)
        entities = {}
        for ent in doc.ents:
            span = ent.start_char, ent.end_char
            entity_id = ent.kb_id_ if ent.kb_id_ != "NIL" else None
            snippet = text[span[0]:span[1]]
            if uppercase and snippet.islower():
                continue
            if is_date(snippet):
                continue
            candidates = self.get_candidates(snippet)
            entities[span] = EntityPrediction(span, entity_id, candidates)
        return entities

    def get_candidates(self, text: str) -> Set[str]:
        return {candidate.entity_ for candidate in self.kb.get_candidates(text)}

    def has_entity(self, entity_id: str) -> bool:
        return self.kb.contains_entity(entity_id)
