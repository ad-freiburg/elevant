import numpy as np
from typing import Optional, Dict, Tuple, Iterator

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

    @staticmethod
    def get_whitelist_types(whitelist_type_file: str):
        types = EntityDatabaseReader.read_whitelist_types(whitelist_type_file)
        return types

    def has_entity(self, entity_id: str) -> bool:
        return self.entity_db.contains_entity(entity_id)

    def get_mention_spans(self, doc: Doc, text: str) -> Iterator[Tuple[Tuple[int, int], str]]:
        for n_tokens in range(self.max_tokens, 0, -1):
            for result in self.get_mention_spans_with_n_tokens(doc, text, n_tokens):
                yield result

    @staticmethod
    def get_mention_spans_with_n_tokens(doc: Doc,
                                        text: str,
                                        n_tokens: int) -> Iterator[Tuple[Tuple[int, int], str]]:
        mention_start = 0
        while mention_start + n_tokens < len(doc):
            span = doc[mention_start].idx, doc[mention_start + n_tokens - 1].idx + len(
                doc[mention_start + n_tokens - 1])
            mention_text = text[span[0]:span[1]]
            yield span, mention_text
            mention_start += 1

    def get_matching_entity_id(self, mention_text: str) -> Optional[str]:
        if mention_text in self.entity_db.link_frequencies:
            # Get matching entity ids for given mention text in order of their link frequency
            entity_id = max(self.entity_db.link_frequencies[mention_text],
                            key=self.entity_db.link_frequencies[mention_text].get)
            # Return the with the highest link frequency that has a whitelist type and
            # a synonym matching the mention text
            if (not self.whitelist_types or self.has_whitelist_type(entity_id)) and mention_text in \
                    self.entity_db.get_entity(entity_id).synonyms:
                return entity_id
        return None

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
        for span, mention_text in self.get_mention_spans(doc, text):
            if uppercase and mention_text.islower():
                continue
            # Do not allow overlapping links. Prioritize links with more tokens
            if np.sum(annotated_chars[span[0]:span[1]]) != 0:
                continue
            predicted_entity_id = self.get_matching_entity_id(mention_text)
            if predicted_entity_id:
                annotated_chars[span[0]:span[1]] = True
                candidates = {predicted_entity_id}
                predictions[span] = EntityPrediction(span, predicted_entity_id, candidates)
        return predictions
