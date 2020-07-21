from typing import Dict, Tuple, Optional, Set
from enum import Enum

import pickle
import spacy
from spacy.tokens import Doc

from src.abstract_entity_linker import AbstractEntityLinker
from src.entity_prediction import EntityPrediction
from src.entity_database_new import EntityDatabase
from src import settings
from src.settings import NER_IGNORE_TAGS
from src.ner_postprocessing import shorten_entities


class LinkingStrategy(Enum):
    LINK_FREQUENCY = 0
    ENTITY_SCORE = 1


class AliasEntityLinker(AbstractEntityLinker):
    LINKER_IDENTIFIER = "ALIAS"

    def __init__(self,
                 entity_database: EntityDatabase,
                 strategy: LinkingStrategy,
                 load_model: bool = True):
        self.entity_db = entity_database
        self.strategy = strategy
        if load_model:
            self.model = spacy.load(settings.LARGE_MODEL_NAME)
            self.model.add_pipe(shorten_entities, name="shorten_ner", after="ner")

    def has_entity(self, entity_id: str) -> bool:
        return self.entity_db.contains_entity(entity_id)

    def _score_entity_by_link_frequency(self, alias: str, entity_id: str) -> int:
        return self.entity_db.get_link_frequency(alias, entity_id)

    def _score_entity_by_score(self, entity_id: str) -> int:
        return self.entity_db.get_score(entity_id)

    def score_entity(self, alias: str, entity_id: str) -> int:
        if self.strategy == LinkingStrategy.LINK_FREQUENCY:
            return self._score_entity_by_link_frequency(alias, entity_id)
        elif self.strategy == LinkingStrategy.ENTITY_SCORE:
            return self._score_entity_by_score(entity_id)
        else:
            raise NotImplementedError("AliasEntityLinker: Strategy %s not implemented." % str(self.strategy))

    def select_entity(self, alias: str, candidates: Set[str]) -> Optional[str]:
        if len(candidates) == 0:
            return None
        scored_entities = [
            (self.score_entity(alias, candidate), candidate) for candidate in candidates
        ]
        score, entity_id = max(scored_entities)
        return entity_id

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
            snippet = text[span[0]:span[1]]
            candidates = self.entity_db.get_candidates(snippet)
            predicted_entity_id = self.select_entity(snippet, candidates)
            predictions[span] = EntityPrediction(span, predicted_entity_id, candidates)
        return predictions
