import numpy as np
from typing import Optional, Dict, Tuple, Iterator, Any

import spacy
from spacy.tokens import Doc

from elevant.helpers.entity_database_reader import EntityDatabaseReader
from elevant.linkers.abstract_entity_linker import AbstractEntityLinker
from elevant.models.entity_database import EntityDatabase
from elevant.models.entity_prediction import EntityPrediction
from elevant import settings
from elevant.utils.offset_converter import OffsetConverter
import logging

logger = logging.getLogger("main." + __name__.split(".")[-1])


class PriorLinker(AbstractEntityLinker):
    def __init__(self, entity_database: EntityDatabase, config: Dict[str, Any]):
        self.entity_db = entity_database
        self.model = spacy.load(settings.LARGE_MODEL_NAME, disable=["lemmatizer"])

        # Get config variables
        self.linker_identifier = config["linker_name"] if "linker_name" in config else "Prior"
        self.ner_identifier = self.linker_identifier
        whitelist_type_file = config["whitelist_type_file"] if "whitelist_type_file" in config \
            else settings.WHITELIST_FILE
        self.use_pos = config["use_pos"] if "use_pos" in config else True

        self.whitelist_types = {}
        if whitelist_type_file:
            self.whitelist_types = self.get_whitelist_types(whitelist_type_file)
        self.max_tokens = 15

    @staticmethod
    def get_whitelist_types(whitelist_type_file: str):
        return EntityDatabaseReader.read_whitelist_types(whitelist_type_file)

    def fix_capitalization(self, doc, text):
        new_text = ""
        lower_sents = dict()
        for tok in doc:
            window_start = max(tok.idx - 30, 0)
            context = text[window_start:tok.idx]
            num_alpha = len([c for c in context if c.isalpha()])
            num_upperalpha = len([c for c in context if c.isalpha() and c.isupper()])
            upper_percentage = num_upperalpha / num_alpha * 100 if num_alpha > 0 else 100
            if tok.text.isupper() and (len(tok) > 3 or (upper_percentage > 70)):
                sent_span = tok.sent[0].idx, tok.sent[-1].idx + len(tok.sent[-1])
                if sent_span not in lower_sents:
                    # Spacy tags PROPN too rigorously when text is all caps, but true
                    # proper nouns are often recognized even when they are lowercased.
                    lower_sent = self.model(text[sent_span[0]:sent_span[1]].lower())
                    lower_sents[sent_span] = lower_sent
                else:
                    lower_sent = lower_sents[sent_span]
                idx_in_sent = OffsetConverter.get_token_idx_in_sent(tok.idx, doc)

                # Tokenization of lower_sent can differ from doc in rare cases.
                # Make sure indices are in range.
                if idx_in_sent >= len(lower_sent) or lower_sent[idx_in_sent].text != tok.text.lower():
                    if idx_in_sent < len(lower_sent):
                        for i, t in enumerate(lower_sent):
                            if t.text == tok.text.lower():
                                idx_in_sent = i

                if idx_in_sent < len(lower_sent) and lower_sent[idx_in_sent].pos_ == "PROPN":
                    new_text += tok.text[0] + tok.text[1:].lower()
                else:
                    new_text += tok.text.lower()
            else:
                new_text += tok.text
            new_text += tok.whitespace_
        return new_text

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
        while mention_start + n_tokens <= len(doc):
            mention_end = mention_start + n_tokens
            span = doc[mention_start].idx, doc[mention_end - 1].idx + len(
                doc[mention_end - 1])
            mention_text = text[span[0]:span[1]]
            # Don't yield mention if directly adjacent tokens are proper nouns
            skip = False
            contains_noun = False
            if self.use_pos:
                if mention_start > 0 and doc[mention_start - 1].pos_ == "PROPN" and len(doc[mention_start - 1]) > 1:
                    skip = True
                if mention_end < len(doc) and doc[mention_end].pos_ == "PROPN" and len(doc[mention_end]) > 1:
                    skip = True
                contains_noun = [True for tok in doc[mention_start:mention_end] if tok.pos_ in ["PROPN", "NOUN"]]
            # For the pos-prior linker, require at least one noun in the mention tokens
            if not skip and len(mention_text) > 1:
                # Only consider span as mention span if it contains at least one noun
                yield span, mention_text, n_tokens, contains_noun
            mention_start += 1

    def get_matching_entity_id(self, mention_text: str, is_sent_start: bool, contains_noun: bool) -> Optional[str]:
        if mention_text in self.entity_db.link_frequencies:
            # Get matching entity ids for given mention text in order of their link frequency
            entity_id = max(self.entity_db.link_frequencies[mention_text],
                            key=self.entity_db.link_frequencies[mention_text].get)
            is_uppercase = mention_text[0].isupper()
            # Return the with the highest link frequency that has a whitelist type and
            # a synonym matching the mention text
            if (not self.whitelist_types or self.has_whitelist_type(entity_id)) and \
                    ((is_uppercase and not is_sent_start) or
                     (self.has_synonym(entity_id, mention_text, is_sent_start) and contains_noun)):
                return entity_id
        return None

    def has_synonym(self, entity_id: str, mention_text: str, is_sent_start: bool) -> bool:
        """ Check if the given mention text is a synonym of the entity with the given ID.
        Returns true also if the mention starts at a sentence start and the mention text
        starting with a lower case letter is a synonym.
        """
        lower_mention_text = mention_text[0].lower() + mention_text[1:]
        return mention_text in self.entity_db.get_entity_aliases(entity_id) or \
               (is_sent_start and lower_mention_text in self.entity_db.get_entity_aliases(entity_id))

    def has_whitelist_type(self, entity_id: str) -> bool:
        types = self.entity_db.get_entity_types(entity_id)
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

        text = self.fix_capitalization(doc, text)
        doc = self.model(text)

        predictions = {}
        annotated_chars = np.zeros(shape=len(text), dtype=int)
        spans = {}
        for span, mention_text, n_tokens, contains_noun in self.get_mention_spans(doc, text):
            if uppercase and mention_text.islower():
                continue
            is_sent_start = OffsetConverter.get_token(span[0], doc).is_sent_start
            predicted_entity_id = self.get_matching_entity_id(mention_text, is_sent_start, contains_noun)
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

                elif n_tokens == 1 and span[0] >= 2 and annotated_chars[span[0] - 2] != 0:
                    # Do not allow two consecutive mentions that are only separated by a single character
                    # (usually a whitespace or a hyphen).
                    # Usually this means that a bigger mention could not be correctly identified.
                    # Delete both mentions.
                    # This does not prevent cases where a proper noun is directly preceding an entity but was not linked
                    preceding_span, preceding_n_tokens = spans[annotated_chars[span[0] - 2]]
                    if preceding_n_tokens == 1:
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
