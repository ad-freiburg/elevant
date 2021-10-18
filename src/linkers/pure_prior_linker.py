import numpy as np
from typing import Optional, Dict, Tuple, List

import spacy
from spacy.tokens import Doc

from src.helpers.entity_database_reader import EntityDatabaseReader
from src.linkers.abstract_entity_linker import AbstractEntityLinker
from src.models.entity_database import EntityDatabase
from src.models.entity_prediction import EntityPrediction
from src import settings


class PurePriorLinker(AbstractEntityLinker):
    LINKER_IDENTIFIER = "PurePrior"

    def __init__(self,
                 entity_database: EntityDatabase,
                 whitelist_type_file: str):
        self.entity_db = entity_database
        self.model = spacy.load(settings.LARGE_MODEL_NAME)
        self.max_tokens = 15
        self.whitelist_types = {}
        if whitelist_type_file:
            self.whitelist_types = self.get_whitelist_types(whitelist_type_file)
        self.prefixes = set()
        self._compute_prefixes()

    def get_whitelist_types(self, whitelist_type_file: str):
        types = EntityDatabaseReader.read_whitelist_types(whitelist_type_file)
        return types

    def has_entity(self, entity_id: str) -> bool:
        return self.entity_db.contains_entity(entity_id)

    @staticmethod
    def token_span_to_char_span(doc: Doc,
                                token_span_start: int,
                                token_span_end: int) -> Tuple[int, int]:
        """The token span end is included."""
        span = doc[token_span_start].idx, doc[token_span_end].idx + len(doc[token_span_end])
        return span

    def _compute_prefixes(self):
        print("computing prefixes...")
        for ai, alias in enumerate(self.entity_db.aliases):
            if ai % 1000 == 0:
                print(f"\r{ai}/{len(self.entity_db.aliases)} aliases", end="")
            alias_doc = self.model(alias)
            n_tokens = len(alias_doc)
            for i in range(n_tokens - 1):
                span = PurePriorLinker.token_span_to_char_span(alias_doc, 0, i)
                prefix = alias[span[0]:span[1]]
                self.prefixes.add(prefix)

    def get_mention_spans(self,
                          doc: Doc,
                          text: str) -> List[Tuple[Tuple[int, int], str]]:
        """The resulting spans can overlap."""
        mention_spans = []
        print("text:", text)
        for start in range(len(doc)):
            print(f"start at position {start}")
            length = 0
            while start + length < len(doc):
                span = PurePriorLinker.token_span_to_char_span(doc, start, start + length)
                span_text = text[span[0]:span[1]]
                if self.entity_db.contains_alias(span_text):
                    print(f"{span_text} is alias")
                    mention_spans.append((span, span_text))
                if span_text not in self.prefixes:
                    break
                print(f"{span_text} is prefix")
                length += 1
        return mention_spans

    def get_matching_entity_id(self, mention_text: str) -> Optional[str]:
        if self.entity_db.contains_alias(mention_text):
            return max(self.entity_db.get_candidates(mention_text),
                       key=lambda candidate: self.entity_db.get_link_frequency(mention_text, candidate))

    def has_whitelist_type(self, entity_id: str) -> bool:
        if self.entity_db.contains_entity(entity_id):
            types = self.entity_db.get_entity(entity_id).type.split("|")
            for typ in types:
                if typ in self.whitelist_types:
                    return True
        return False

    def predict(self,
                text: str,
                doc: Optional[Doc] = None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
        if doc is None:
            doc = self.model(text)

        predictions = {}
        annotated_chars = np.zeros(shape=len(text), dtype=bool)
        mention_spans = self.get_mention_spans(doc, text)
        mention_spans = sorted(mention_spans, key=lambda span: span[0][1] - span[0][0], reverse=True)
        for span, mention_text in mention_spans:
            if uppercase and mention_text.islower():
                continue
            predicted_entity_id = self.get_matching_entity_id(mention_text)
            if predicted_entity_id:
                # Do not allow overlapping links. Prioritize links with more tokens
                if np.sum(annotated_chars[span[0]:span[1]]) == 0:
                    if not self.whitelist_types or self.has_whitelist_type(predicted_entity_id):
                        annotated_chars[span[0]:span[1]] = True
                        candidates = {predicted_entity_id}
                        predictions[span] = EntityPrediction(span, predicted_entity_id, candidates)
        return predictions
