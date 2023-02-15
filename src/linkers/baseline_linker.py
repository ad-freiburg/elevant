from typing import Dict, Tuple, Optional, Set, List, Any

import spacy
from spacy.tokens import Doc

from src.linkers.abstract_entity_linker import AbstractEntityLinker
from src.models.entity_prediction import EntityPrediction
from src.models.entity_database import EntityDatabase
from src import settings
from src.settings import NER_IGNORE_TAGS
from src.ner.maximum_matching_ner import MaximumMatchingNER
from src.utils.dates import is_date
import src.ner.ner_postprocessing  # import is needed so Python finds the custom factory


class BaselineLinker(AbstractEntityLinker):
    def __init__(self,
                 entity_database: EntityDatabase,
                 config: Dict[str, Any]):
        self.entity_db = entity_database

        # Get config variables
        self.linker_identifier = config["linker_name"] if "linker_name" in config else "Baseline"
        self.strategy = config["strategy"] if "strategy" in config else "wikipedia"
        self.longest_alias_ner = config["longest_alias_ner"] if "longest_alias_ner" in config else False
        self.ner_identifier = "LongestAliasNER" if self.longest_alias_ner else "EnhancedSpacy"

        self.ner = None
        if self.longest_alias_ner:
            self.ner = MaximumMatchingNER(entity_database)
            self.model = None
        else:
            self.model = spacy.load(settings.LARGE_MODEL_NAME)
            self.model.add_pipe("ner_postprocessor", after="ner")

    def has_entity(self, entity_id: str) -> bool:
        return self.entity_db.contains_entity(entity_id)

    def _score_entity_by_link_frequency(self, alias: str, entity_id: str) -> int:
        return self.entity_db.get_link_frequency(alias, entity_id)

    def _score_entity_by_score(self, entity_id: str) -> int:
        return self.entity_db.get_sitelink_count(entity_id)

    def score_entity(self, alias: str, entity_id: str) -> int:
        if self.strategy == "wikipedia":
            return self._score_entity_by_link_frequency(alias, entity_id)
        elif self.strategy == "wikidata":
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
