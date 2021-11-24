import numpy as np
from typing import Optional, Dict, Tuple, Iterator

import spacy
from spacy.tokens import Doc

from src.helpers.entity_database_reader import EntityDatabaseReader
from src.linkers.abstract_entity_linker import AbstractEntityLinker
from src.models.entity_database import EntityDatabase
from src.models.entity_prediction import EntityPrediction
from src import settings
from src.utils.offset_converter import OffsetConverter


class PriorLinker(AbstractEntityLinker):
    LINKER_IDENTIFIER = "PURE_PRIOR_LINKER"

    def __init__(self,
                 entity_database: EntityDatabase,
                 whitelist_type_file: str,
                 use_pos: bool):
        self.entity_db = entity_database
        self.model = spacy.load(settings.LARGE_MODEL_NAME)
        self.max_tokens = 15
        self.whitelist_types = {}
        if whitelist_type_file:
            self.whitelist_types = self.get_whitelist_types(whitelist_type_file)
        self.use_pos = use_pos
        if self.use_pos:
            PriorLinker.LINKER_IDENTIFIER = "POS_PRIOR_LINKER"

    @staticmethod
    def get_whitelist_types(whitelist_type_file: str):
        return EntityDatabaseReader.read_whitelist_types(whitelist_type_file)

    def has_entity(self, entity_id: str) -> bool:
        return self.entity_db.contains_entity(entity_id)

    def get_mention_spans(self, doc: Doc, text: str) -> Iterator[Tuple[Tuple[int, int], str]]:
        for n_tokens in range(self.max_tokens, 0, -1):
            for result in self.get_mention_spans_with_n_tokens(doc, text, n_tokens):
                yield result

    def get_mention_spans_with_n_tokens(self,
                                        doc: Doc,
                                        text: str,
                                        n_tokens: int) -> Iterator[Tuple[Tuple[int, int], str]]:
        mention_start = 0
        while mention_start + n_tokens < len(doc):
            span = doc[mention_start].idx, doc[mention_start + n_tokens - 1].idx + len(
                doc[mention_start + n_tokens - 1])
            mention_text = text[span[0]:span[1]]
            # For the pos_prior linker, require at least one noun in the mention tokens
            if not self.use_pos or [True for tok in doc[mention_start:mention_start + n_tokens]
                                    if tok.pos_ in ["PROPN", "NOUN"]]:
                # Only consider span as mention span if it contains at least one noun
                yield span, mention_text, n_tokens
            mention_start += 1

    def get_matching_entity_id(self, mention_text: str, is_sent_start: bool) -> Optional[str]:
        if mention_text in self.entity_db.link_frequencies:
            # Get matching entity ids for given mention text in order of their link frequency
            entity_id = max(self.entity_db.link_frequencies[mention_text],
                            key=self.entity_db.link_frequencies[mention_text].get)
            # Return the with the highest link frequency that has a whitelist type and
            # a synonym matching the mention text
            if (not self.whitelist_types or self.has_whitelist_type(entity_id)) and \
                    self.has_synonym(entity_id, mention_text, is_sent_start):
                return entity_id
        return None

    def has_synonym(self, entity_id: str, mention_text: str, is_sent_start: bool) -> bool:
        """ Check if the given mention text is a synonym of the entity with the given ID.
        Returns true also if the mention starts at a sentence start and the mention text
        starting with a lower case letter is a synonym.
        """
        lower_mention_text = mention_text[0].lower() + mention_text[1:]
        return mention_text in self.entity_db.get_entity(entity_id).synonyms or \
               (is_sent_start and lower_mention_text in self.entity_db.get_entity(entity_id).synonyms)

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
        annotated_chars = np.zeros(shape=len(text), dtype=int)
        spans = {}
        for span, mention_text, n_tokens in self.get_mention_spans(doc, text):
            if uppercase and mention_text.islower():
                continue
            is_sent_start = OffsetConverter.get_token(span[0], doc).is_sent_start
            predicted_entity_id = self.get_matching_entity_id(mention_text, is_sent_start)
            if predicted_entity_id:
                if np.sum(annotated_chars[span[0]:span[1]]) != 0:
                    # Do not allow overlapping links. Prioritize links with more tokens and resolve ties by link
                    # frequency. This works, because spans are sorted by number of tokens and then from left to right.
                    overlap_indices = np.nonzero(annotated_chars[span[0]:span[1]])[0]
                    overlap_span, overlap_n_tokens = spans[annotated_chars[span[0]:span[1]][overlap_indices[0]]]
                    overlap_prediction = predictions[overlap_span]
                    overlap_mention_text = text[overlap_prediction.span[0]:overlap_prediction.span[1]]
                    overlap_link_frequency = self.entity_db.link_frequencies[overlap_mention_text] \
                        [overlap_prediction.entity_id]
                    curr_link_frequency = self.entity_db.link_frequencies[mention_text][predicted_entity_id]
                    if overlap_n_tokens == n_tokens and overlap_link_frequency < curr_link_frequency:
                        # Remove previous predicted entity
                        del predictions[overlap_prediction.span]
                        del spans[overlap_prediction.span[0] + 1]
                        annotated_chars[overlap_prediction.span[0]:overlap_prediction.span[1]] = 0
                    else:
                        # Skip current predicted entity
                        continue

                elif span[0] >= 2 and annotated_chars[span[0] - 2] != 0:
                    # Do not allow two consecutive mentions that are only separated by a single character
                    # (usually a whitespace or a hyphen).
                    # Usually this means that a bigger mention could not be correctly identified.
                    # Delete both mentions.
                    # This does not prevent cases where a proper noun is directly preceding an entity but was not linked
                    preceding_span, _ = spans[annotated_chars[span[0] - 2]]
                    annotated_chars[preceding_span[0]:preceding_span[1]] = 0
                    del predictions[preceding_span]
                    del spans[preceding_span[0] + 1]
                    continue

                # Add new prediction
                # +1 so we can use sum to detect overlaps (span[0] can be 0)
                annotated_chars[span[0]:span[1]] = span[0] + 1
                candidates = {predicted_entity_id}
                predictions[span] = EntityPrediction(span, predicted_entity_id, candidates)
                spans[span[0] + 1] = span, n_tokens  # there are no overlaps so span starts uniquely determine a span
        return predictions
