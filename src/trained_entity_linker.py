from typing import Dict, Tuple, Set, Optional

from spacy.tokens import Doc
from spacy.language import Language

from src.abstract_entity_linker import AbstractEntityLinker
from src.entity_linker_loader import EntityLinkerLoader
from src.entity_prediction import EntityPrediction
from src.settings import NER_IGNORE_TAGS
from src.entity_database import EntityDatabase
from src.ner_postprocessing import NERPostprocessor
from src.dates import is_date


class TrainedEntityLinker(AbstractEntityLinker):
    LINKER_IDENTIFIER = "LINKER"

    def __init__(self,
                 name: str,
                 entity_db: EntityDatabase,
                 model: Optional[Language] = None,
                 kb_name: Optional[str] = None):
        if model is None:
            self.model = EntityLinkerLoader.load_trained_linker(name, kb_name=kb_name)
            if not self.model.has_pipe("ner_postprocessor"):
                ner_postprocessor = NERPostprocessor(entity_db)
                self.model.add_pipe(ner_postprocessor, name="ner_postprocessor", after="ner")
        else:
            self.model = model
            self.model.add_pipe(EntityLinkerLoader.load_entity_linker(name, kb_name=kb_name))
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
        return {candidate.entity_ for candidate in self.kb.get_candidates(snippet)}

    def contains_entity(self, entity_id):
        return entity_id in self.known_entities
