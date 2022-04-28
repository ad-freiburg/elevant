from typing import Dict, Tuple, Optional, Set, List
from enum import Enum

import spacy
from spacy.tokens import Doc

from src.linkers.abstract_entity_linker import AbstractEntityLinker
from src.models.entity_prediction import EntityPrediction
from src.models.entity_database import EntityDatabase
from src import settings
from src.settings import NER_IGNORE_TAGS
from src.ner.ner_postprocessing import NERPostprocessor
from src.ner.maximum_matching_ner import MaximumMatchingNER
from src.utils.dates import is_date


class LinkingStrategy(Enum):
    LINK_FREQUENCY = 0
    ENTITY_SCORE = 1


class AliasEntityLinker(AbstractEntityLinker):
    LINKER_IDENTIFIER = "ALIAS"

    def __init__(self,
                 entity_database: EntityDatabase,
                 strategy: LinkingStrategy,
                 load_model: bool = True,
                 longest_alias_ner: bool = False):
        self.entity_db = entity_database
        self.strategy = strategy
        self.longest_alias_ner = longest_alias_ner
        self.ner = MaximumMatchingNER(entity_database)
        if load_model:
            self.model = spacy.load(settings.LARGE_MODEL_NAME)
            ner_postprocessor = NERPostprocessor(self.entity_db)
            self.model.add_pipe(ner_postprocessor, name="ner_postprocessor", after="ner")
        else:
            self.model = None

    def has_entity(self, entity_id: str) -> bool:
        return self.entity_db.contains_entity(entity_id)

    def _score_entity_by_link_frequency(self, alias: str, entity_id: str) -> int:
        return self.entity_db.get_link_frequency(alias, entity_id)

    def _score_entity_by_score(self, entity_id: str) -> int:
        return self.entity_db.get_sitelink_count(entity_id)

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

    def entity_spans(self, text: str, doc: Optional[Doc]) -> List[Tuple[int, int]]:
        if self.longest_alias_ner:
            return self.ner.entity_mentions(text)
        else:
            spans = []
            for ent in doc.ents:
                if ent.label_ in NER_IGNORE_TAGS:
                    continue
                spans.append((ent.start_char, ent.end_char))
            return spans

    def predict(self,
                text: str,
                doc: Optional[Doc] = None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
        if doc is None and self.model is not None:
            doc = self.model(text)
        predictions = {}
        for span in self.entity_spans(text, doc):
            snippet = text[span[0]:span[1]]
            if uppercase and snippet.islower():
                continue
            if is_date(snippet):
                continue
            candidates = self.entity_db.get_candidates(snippet)
            predicted_entity_id = self.select_entity(snippet, candidates)
            predictions[span] = EntityPrediction(span, predicted_entity_id, candidates)
        return predictions
