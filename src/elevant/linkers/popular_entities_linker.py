from typing import Dict, Tuple, List, Optional, Set, Any

import logging
import pygtrie
import spacy
from spacy.tokens import Doc

from elevant.evaluation.groundtruth_label import GroundtruthLabel
from elevant.linkers.abstract_entity_linker import AbstractEntityLinker
from elevant.models.entity_mention import EntityMention
from elevant.models.entity_prediction import EntityPrediction
from elevant.ner.maximum_matching_ner import MaximumMatchingNER
from elevant.settings import NER_IGNORE_TAGS
from elevant.models.entity_database import EntityDatabase
from elevant.utils.dates import is_date
from elevant import settings
from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper, UnknownEntity
from elevant.utils.offset_converter import OffsetConverter
import elevant.ner.ner_postprocessing  # import is needed so Python finds the custom factory
import elevant.utils.custom_sentencizer  # import is needed so Python finds the custom component

logger = logging.getLogger("main." + __name__.split(".")[-1])


def overlaps_with_linked_entity(span: Tuple[int, int], linked_entities: Dict[Tuple[int, int], EntityMention]) -> bool:
    for linked_span in sorted(linked_entities):
        if linked_span[0] >= span[1]:
            # linked spans are sorted so we can break the loop as soon as the start
            # of a already linked span is >= the end of the predicted span
            return False
        if linked_span[1] > span[0]:
            # Start of linked span is smaller than the end of the predicted span and
            # the end of the linked span is greater than the start of the predicted span
            return True
    return False


class PopularEntitiesLinker(AbstractEntityLinker):
    def __init__(self, entity_db: EntityDatabase, config: Dict[str, Any]):
        self.entity_db = entity_db

        # Get config variables
        self.linker_identifier = config["linker_name"] if "linker_name" in config else "Popular Entities"
        self.min_score = config["min_score"] if "min_score" in config else 15
        self.longest_alias_ner = config["longest_alias_ner"] if "longest_alias_ner" in config else False
        self.ner_identifier = "LongestAliasNER" if self.longest_alias_ner else "EnhancedSpacy"

        if self.longest_alias_ner:
            self.ner = MaximumMatchingNER(self.entity_db)

        self.model = spacy.load(settings.LARGE_MODEL_NAME, disable=["lemmatizer"])
        self.model.add_pipe("custom_sentencizer", before="parser")
        self.model.add_pipe("ner_postprocessor", after="ner")

        # Create a prefix trie to speed up lowercase entity detection
        logger.info("Building prefix trie for detection of lowercase entities...")
        self.trie = pygtrie.StringTrie(separator=" ")
        for i, (entity_name, qids) in enumerate(entity_db.name_to_entities_db.items()):
            if entity_name.islower():
                if len(qids) == 1:
                    self.trie[entity_name] = next(iter(qids))
                else:
                    max_entity = None, -1
                    for qid in qids:
                        score = entity_db.get_sitelink_count(qid)
                        if score > max_entity[1]:
                            max_entity = qid, score
                    self.trie[entity_name] = max_entity[0]
        logger.info(f"Built prefix trie with {len(self.trie)} non-named entities.")

    def entity_spans(self, text: str, doc: Optional[Doc]) -> List[Tuple[Tuple[int, int], bool, bool]]:
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
                if self.entity_db.is_language(snippet) and token.dep_ == "pobj" and span[0] >= 3 and\
                        text[span[0] - 3:span[0] - 1].lower() == "in":
                    is_language = True
                # TODO: If we want to use MaxMatchingNER, whether a mention refers to a person could
                #       be determined by a set of first names, e.g. extracted from qid_to_name.tsv
                is_person = False
                spans.append((span, is_language, is_person))
        else:
            # Use Spacy NER
            for ent in doc.ents:
                if ent.label_ in NER_IGNORE_TAGS:
                    continue
                spans.append(((ent.start_char, ent.end_char), ent.label_ == "LANGUAGE", ent.label_ == "PERSON"))
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
                         linked_entities: Optional[Dict[Tuple[int, int], EntityMention]] = None) \
            -> Dict[Tuple[int, int], EntityPrediction]:
        if doc is None:
            doc = self.model(text)
        predictions = {}
        unknown_person_name_parts = set()
        prediction_cache = {}
        for span, is_language, is_person in self.entity_spans(text, doc):
            if linked_entities and overlaps_with_linked_entity(span, linked_entities):
                continue
            snippet = text[span[0]:span[1]]
            if snippet in prediction_cache:
                # If the snippet was linked before, use the cache to link it to the same entity
                entity_id, candidates, is_language_cache, is_person_cache = prediction_cache[snippet]
                if is_language_cache == is_language and is_person_cache == is_person:
                    predictions[span] = EntityPrediction(span, entity_id, candidates)
                    continue

            if snippet.islower():
                # Only include snippets recognized by SpaCy that contain uppercase letters
                # since SpaCy's non-named entity recognition is bad (recognizes mostly dates or "year", "season")
                continue
            if is_date(snippet):
                continue
            if snippet in unknown_person_name_parts and is_person:
                # Don't link parts of a person entity that was linked to unknown before
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
                candidates = self.entity_db.get_candidates(snippet)
                entity_id = self.select_entity(name_and_demonym_candidates, candidates)
            if entity_id is None:
                entity_id = UnknownEntity.NIL.value
            candidates.update(name_and_demonym_candidates)
            predictions[span] = EntityPrediction(span, entity_id, candidates)
            prediction_cache[snippet] = (entity_id, candidates, is_language, is_person)

            # Store entity mention text if no entity could be predicted, and it is likely a human name
            # to avoid linking parts of it later.
            if KnowledgeBaseMapper.is_unknown_entity(entity_id) and " " in snippet and is_person:
                first_name = snippet.split()[0]
                last_name = snippet.split()[-1]
                unknown_person_name_parts.add(first_name)
                unknown_person_name_parts.add(last_name)
        predictions.update(self.get_lowercase_predictions(linked_entities, predictions, doc, text))
        return predictions

    def get_lowercase_predictions(self, linked_entities, predictions, doc, text):
        linked_entities.update(predictions)
        lowercase_predictions = {}
        i = 0
        while i < len(doc):
            tok = doc[i]
            if not tok.text.islower() or tok.is_stop or tok.is_punct:
                # First word of a non-named entity cannot be a stopword or punctuation
                i += 1
                continue

            span_end = tok.idx + len(tok.text)
            snippet = text[tok.idx:span_end]
            last_snippet_in_trie = None
            last_snippet_in_trie_j = -1
            j = i + 1

            while self.trie.has_subtrie(snippet) and j < len(doc):
                new_tok = doc[j]
                new_span_end = new_tok.idx + len(new_tok.text)
                if self.is_snippet_variant_in_trie(snippet):
                    last_snippet_in_trie = snippet
                    last_snippet_in_trie_j = j
                snippet += text[span_end:new_span_end]
                span_end = new_span_end
                j += 1
            if self.is_snippet_variant_in_trie(snippet):
                # has_subtrie(snippet) is False if the only key with the prefix snippet
                # is snippet so I need this check here
                entity_id = self.get_entity_from_trie(snippet)
            elif last_snippet_in_trie is not None:
                entity_id = self.get_entity_from_trie(last_snippet_in_trie)
                snippet = last_snippet_in_trie
                j = last_snippet_in_trie_j
            else:
                i += 1
                continue

            span = tok.idx, tok.idx + len(snippet)
            tokens = [t for t in doc[i:j]]

            if overlaps_with_linked_entity(span, linked_entities):
                i += 1
                continue

            pos = set(t.pos_ for t in tokens)
            if not pos.intersection({"NOUN"}):
                i += 1
                continue

            sitelink_count = self.entity_db.get_sitelink_count(entity_id)
            if sitelink_count >= self.min_score and \
                    self.entity_db.get_entity_types(entity_id) != [GroundtruthLabel.OTHER]:
                # This is not the same as simply excluding these entities from the prefix trie.
                # This way, entities are skipped if they exist, but don't have the correct type
                # or required min score. Otherwise, parts of the entity could be linked.
                if entity_id is None:
                    entity_id = UnknownEntity.NIL.value
                lowercase_predictions[span] = EntityPrediction(span, entity_id, {entity_id})
            i = j + 1
        return lowercase_predictions

    def is_snippet_variant_in_trie(self, snippet: str) -> bool:
        """
        Returns true if the snippet or a potential singular form of it is in
        the trie.
        """
        return snippet in self.trie or (snippet[-1] == "s" and snippet[:-1] in self.trie)

    def get_entity_from_trie(self, snippet: str) -> str:
        """
        Returns the entity ID for the given snippet (or its singular form)
        from the trie
        """
        return self.trie[snippet] if snippet in self.trie else self.trie[snippet[:-1]]

    def select_entity(self, name_and_demonym_candidates: Set[str], candidates: Set[str]) -> str:
        """
        Select the entity from the set of candidates that has the highest sitelink count.
        If none of the entities has a sitelink count > self.min_score return None.
        """
        highest_sitelink_count_entity = None
        highest_sitelink_count = 0
        # Sort for reproducibility. Names and demonyms are preferred over aliases with same sitelink count
        for entity_id in sorted(name_and_demonym_candidates) + sorted(candidates):
            sitelink_count = self.entity_db.get_sitelink_count(entity_id)
            if sitelink_count >= self.min_score and sitelink_count > highest_sitelink_count:
                highest_sitelink_count_entity = entity_id
                highest_sitelink_count = sitelink_count
        return highest_sitelink_count_entity

    def has_entity(self, entity_id: str) -> bool:
        return self.entity_db.contains_entity(entity_id)
