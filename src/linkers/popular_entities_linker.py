from typing import Dict, Tuple, List, Optional, Set

import spacy
from spacy.tokens import Doc

from src.linkers.abstract_entity_linker import AbstractEntityLinker
from src.models.entity_mention import EntityMention
from src.models.entity_prediction import EntityPrediction
from src.ner.maximum_matching_ner import MaximumMatchingNER
from src.settings import NER_IGNORE_TAGS
from src.models.entity_database import EntityDatabase
from src.ner.ner_postprocessing import NERPostprocessor
from src.utils.dates import is_date
from src import settings
from src.utils.offset_converter import OffsetConverter


def get_non_overlapping_span(span: Tuple[int, int],
                             linked_entities: Dict[Tuple[int, int], EntityMention],
                             text: str) -> Optional[Tuple[int, int]]:
    for linked_span in sorted(linked_entities):
        if linked_span[0] > span[1]:
            # linked spans are sorted so we can break the loop as soon as the start
            # of a already linked span is greater than the end of the predicted span
            break
        if linked_span[0] <= span[0] and linked_span[1] >= span[1]:
            # Return None if the already linked span completely covers the predicted span
            return None
        if span[0] < linked_span[0] < span[1]:
            # span starts before the already linked span and overlaps with it
            end = linked_span[0]
            while not text[end - 1].isalpha():
                end -= 1
            for ending in ("'s", "'"):
                # Trim possessive suffixes from span
                if text[span[0]:end].endswith(ending):
                    end = end - len(ending)
            span = span[0], end
        elif False and linked_span[0] <= span[0] < linked_span[1]:
            # TODO: Not sure if this case ever occurs and makes sense
            # span starts after the already linked span and overlaps with it
            start = linked_span[1] + 1
            while not text[start].isalpha():
                start += 1
            span = start, span[1]
    return span


class PopularEntitiesLinker(AbstractEntityLinker):
    LINKER_IDENTIFIER = "POPULAR_ENTITIES_LINKER"

    def __init__(self,
                 min_score: int,
                 entity_db: EntityDatabase,
                 longest_alias_ner: Optional[bool] = False):
        self.min_score = min_score
        self.entity_db = entity_db
        self.longest_alias_ner = longest_alias_ner
        self.ner = MaximumMatchingNER(self.entity_db)
        self.model = spacy.load(settings.LARGE_MODEL_NAME)
        ner_postprocessor = NERPostprocessor(self.entity_db)
        self.model.add_pipe(ner_postprocessor, name="ner_postprocessor", after="ner")

    def entity_spans(self, text: str, doc: Optional[Doc]) -> List[Tuple[Tuple[int, int], bool]]:
        """
        Retrieve entity spans from the given text, i.e. perform entity recognition step.
        """
        spans = []
        if self.longest_alias_ner:
            # Use own longest-alias-NER
            original_spans = self.ner.entity_mentions(text)
            for span in original_spans:
                is_language = False
                snippet = text[span[0]:span[1]]
                token = OffsetConverter.get_token(span[0], doc)
                if self.entity_db.is_language(snippet) and token.dep_ == "pobj" and span[0] >= 3 and text[span[0] - 3:span[0] - 1].lower() == "in":
                    is_language = True
                spans.append((span, is_language))
        else:
            # Use Spacy NER
            for ent in doc.ents:
                if ent.label_ in NER_IGNORE_TAGS:
                    continue
                spans.append(((ent.start_char, ent.end_char), ent.label_ == "LANGUAGE"))
        return spans

    def predict(self,
                text: str,
                doc: Optional[Doc] = None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
        return self.predict_globally(text, doc, uppercase, None)

    def predict_globally(self,
                         text: str,
                         doc: Optional[Doc] = None,
                         uppercase: Optional[bool] = False,
                         linked_entities: Optional[Dict[Tuple[int, int], EntityMention]] = None) -> Dict[Tuple[int, int], EntityPrediction]:
        if doc is None:
            doc = self.model(text)
        predictions = {}
        for span, is_language in self.entity_spans(text, doc):
            if linked_entities:
                span = get_non_overlapping_span(span, linked_entities, text)
                if span is None:
                    continue
            snippet = text[span[0]:span[1]]

            if snippet.islower():
                # Only include snippets that contain uppercase letters for this linker
                # since it otherwise makes a lot of abstraction errors
                continue
            if is_date(snippet):
                continue

            candidates = set()
            name_and_demonym_candidates = set()
            if is_language and self.entity_db.is_language(snippet):
                # If NER component determined mention is a language, link to language if it
                # exists in the database
                entity_id = self.entity_db.get_entity_for_language(snippet)
            else:
                if self.entity_db.contains_entity_name(snippet):
                    # Prefer entities where the name matches the mention instead of some alias
                    name_and_demonym_candidates = self.entity_db.get_entities_by_name(snippet)
                if self.entity_db.is_demonym(snippet):
                    # If mention is a demonym, add corresponding entity to candidates
                    # Countries are preferred automatically, since they generally have
                    # a higher sitelink count than languages or ethnicities
                    demonym_entities = self.entity_db.get_entities_for_demonym(snippet)
                    name_and_demonym_candidates.update(demonym_entities)
                entity_id = self.select_entity(name_and_demonym_candidates)
                if entity_id is None:
                    candidates = self.entity_db.get_candidates(snippet)
                    entity_id = self.select_entity(candidates)
            if entity_id is not None:
                candidates.update(name_and_demonym_candidates)
                predictions[span] = EntityPrediction(span, entity_id, candidates)
        return predictions

    def select_entity(self, candidates: Set[str]) -> str:
        """
        Select the entity from the set of candidates that has the highest sitelink count.
        If none of the entities has a sitelink count > self.min_score return None.
        """
        highest_sitelink_count_entity = None
        highest_sitelink_count = 0
        for entity_id in sorted(candidates):  # Sort for reproducibility
            sitelink_count = self.entity_db.get_sitelink_count(entity_id)
            if sitelink_count >= self.min_score and sitelink_count > highest_sitelink_count:
                highest_sitelink_count_entity = entity_id
                highest_sitelink_count = sitelink_count
        return highest_sitelink_count_entity

    def has_entity(self, entity_id: str) -> bool:
        return self.entity_db.contains_entity(entity_id)
