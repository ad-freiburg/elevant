from typing import Dict, Tuple, Optional, Set
from enum import Enum

import pickle
import spacy
from spacy.tokens import Doc

from src.abstract_entity_linker import AbstractEntityLinker
from src.entity_prediction import EntityPrediction
from src.entity_database import EntityDatabase
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
        if self.strategy == LinkingStrategy.LINK_FREQUENCY:
            with open(settings.LINK_FREEQUENCIES_FILE, "rb") as f:
                self.link_frequencies = pickle.load(f)

    def has_entity(self, entity_id: str) -> bool:
        return self.entity_db.contains(entity_id)

    def _score_entity_by_link_frequency(self, alias: str, entity_id: str) -> int:
        if entity_id not in self.entity_db.wikidata2wikipedia:
            return 0
        entity_name = self.entity_db.wikidata2wikipedia[entity_id]
        if alias in self.link_frequencies and entity_name in self.link_frequencies[alias]:
            return self.link_frequencies[alias][entity_name]
        else:
            return 0

    def _score_entity_by_score(self, entity_id: str) -> int:
        return self.entity_db.get_score(entity_id)

    def score_entity(self, alias: str, entity_id: str) -> int:
        if self.strategy == LinkingStrategy.LINK_FREQUENCY:
            return self._score_entity_by_link_frequency(alias, entity_id)
        elif self.strategy == LinkingStrategy.ENTITY_SCORE:
            return self._score_entity_by_score(entity_id)
        else:
            raise NotImplementedError("AliasEntityLinker: Strategy %s not implemented." % str(self.strategy))

    def select_entity(self, alias: str, candidates: Set[str]) -> str:
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
            if self.entity_db.contains_alias(snippet):
                candidates = self.entity_db.get_candidates(snippet)
                predicted_entity_id = self.select_entity(snippet, candidates)
            else:
                candidates = set()
                predicted_entity_id = None
            predictions[span] = EntityPrediction(span, predicted_entity_id, candidates)
        return predictions
