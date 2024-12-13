from typing import Optional, Tuple, List, Set, Dict
from spacy.tokens import Doc, Token
from spacy.language import Language

import spacy
import re
from collections import defaultdict

import elevant.utils.custom_sentencizer  # import is needed so Python finds the custom component
from elevant.linkers.abstract_coref_linker import AbstractCorefLinker
from elevant.models.coref_cluster import CorefCluster
from elevant.utils.dependency_conll_extractor import DependencyConllExtractor
from elevant.models.dependency_graph import EnhancedDependencyGraph
from elevant.models.entity_database import EntityDatabase
from elevant.models.gender import Gender
from elevant.utils.offset_converter import OffsetConverter
from elevant.utils.pronoun_finder import PronounFinder
from elevant.models.article import Article
from elevant import settings


QUOTATION_MARKS = ('"', '“')
DIRECT_SPEECH_MIN_TOKENS = 4


class DirectSpeech:
    def __init__(self,
                 span: Tuple[int, int],
                 speaker: Token):
        self.span = span
        self.speaker = speaker


class ReferencedEntity:
    def __init__(self,
                 span: Tuple[int, int],
                 entity_id: str,
                 gender: Gender,
                 types: Set[str],
                 deps: List[str],
                 direct_speech: DirectSpeech):
        self.span = span
        self.entity_id = entity_id
        self.gender = gender
        self.types = types
        self.deps = deps
        self.direct_speech = direct_speech


def get_direct_speeches(article: Article, doc: Doc) -> List[DirectSpeech]:
    """
    Return a list with direct speeches (span and possible speaker token) for
    the given article.
    """
    paragraph_matches = re.finditer(r"\n\n", article.text)
    paragraph_boundaries = [m.start() for m in paragraph_matches] if paragraph_matches else []

    start_offset = -1
    start_index = -1
    subject = False
    verb = False
    possible_speaker_tok = None
    direct_speeches = []
    for tok in doc:
        if tok.text in QUOTATION_MARKS:
            if start_offset >= 0:
                # Add span to direct speech span if it is a valid direct speech span
                start_ps = [b for b in paragraph_boundaries if start_offset <= b]
                end_ps = [b for b in paragraph_boundaries if tok.idx <= b]
                single_paragraph = True if start_ps and end_ps and start_ps[-1] == end_ps[-1] else False
                if subject and verb and tok.i >= start_index + DIRECT_SPEECH_MIN_TOKENS and single_paragraph:
                    direct_speech = DirectSpeech((start_offset, tok.idx), possible_speaker_tok)
                    direct_speeches.append(direct_speech)

                # Reset direct speech values
                start_offset = -1
                start_index = -1
                subject = False
                verb = False
            else:
                start_offset = tok.idx
                start_index = tok.i
        elif start_offset >= 0:
            # Check whether the current direct speech span is a somewhat valid sentence with subject and a verb
            if tok.dep_ == "nsubj" or tok.dep_ == "nsubjpass":
                subject = True
            if tok.pos_ == "VERB" or tok.pos_ == "AUX":
                verb = True
        elif tok.dep_ == "nsubj":
            possible_speaker_tok = tok
    return direct_speeches


def get_paragraphs(article: Article) -> List[Tuple[int, int]]:
    """
    Return a list of paragraph spans for the given article.
    """
    paragraph_matches = re.finditer(r"\n\n", article.text)
    paragraphs = []
    start = 0
    match = None
    for match in paragraph_matches:
        paragraphs.append((start, match.end()))
        start = match.end() + 1
    if match and match.end() < len(article.text):
        paragraphs.append((start, len(article.text)))
    return paragraphs


def is_first_subj_in_paragraph(tok: Token, paragraphs: List[Tuple[int, int]], doc: Doc) -> bool:
    """
    Return true if the given token is the first subject in the given paragraph.
    """
    if tok.dep_ not in ('nsubj', 'nsubjpass'):
        return False
    for start, end in paragraphs:
        if start <= tok.idx < end:
            sent = OffsetConverter.get_sentence(start, doc)
            if sent.end_char > tok.idx:
                return True
    return False


def get_containing_direct_speech(offset: int, direct_speeches: List[DirectSpeech]) -> DirectSpeech:
    """
    Return the direct speech that contains the given offset if any.
    """
    for ds in direct_speeches:
        s, e = ds.span
        if s <= offset <= e:
            return ds


class KBCorefLinker(AbstractCorefLinker):
    MAX_NUM_SENTS = -1
    COREF_PREFIXES = ("the", "that", "this")

    def __init__(self, entity_db: EntityDatabase, model: Optional[Language] = None):
        if model is None:
            self.model = spacy.load(settings.LARGE_MODEL_NAME, disable=["lemmatizer"])
            self.model.add_pipe("custom_sentencizer", before="parser")
        else:
            self.model = model
        self.entity_db = entity_db
        self.sent_start_idxs = None
        self.title_entity = None
        self.type_aliases = None

    def get_referenced_entity(self,
                              span: Tuple[int, int],
                              preceding_entities: List[ReferencedEntity],
                              tok_text: str,
                              doc: Optional[Doc] = None,
                              max_distance: Optional[int] = None,
                              type_reference: Optional[bool] = False,
                              direct_speech: Optional[DirectSpeech] = None,
                              neutral_paragraph_subject: Optional[bool] = False) -> Optional[ReferencedEntity]:
        referenced_entity = None
        direct_speech_len = 0
        if neutral_paragraph_subject and self.title_entity and self.title_entity.gender == Gender.NEUTRAL:
            return self.title_entity
        for i, preceding_entity in enumerate(reversed(preceding_entities)):
            pre_span = preceding_entity.span
            if direct_speech and PronounFinder.is_first_person_singular(tok_text):
                # Resolve first person singular references in direct speech to the direct speech speaker entity
                if direct_speech.speaker is None:
                    return
                speaker_s = direct_speech.speaker.idx
                if pre_span[0] <= speaker_s <= pre_span[1]:
                    if preceding_entity.gender in [Gender.MALE, Gender.FEMALE]:
                        return preceding_entity
                    return
                continue
            if not direct_speech and preceding_entity.direct_speech:
                # If reference is not part of direct speech, ignore entities in direct speech spans
                ds_s, ds_e = preceding_entity.direct_speech.span
                direct_speech_len = ds_e - ds_s
                continue
            if pre_span[1] + max_distance + direct_speech_len < span[0]:
                # Direct speech span is not included in max distance unless the reference itself is direct speech
                break
            if i == 0:
                referenced_entity = preceding_entity
            if "nsubj" in preceding_entity.deps or "nsubjpass" in preceding_entity.deps:
                return preceding_entity
        return referenced_entity

    @staticmethod
    def get_preceding_entities(recent_ents_per_sent: List[Dict[Tuple[int, int], ReferencedEntity]],
                               gender: Optional[Gender] = None,
                               typ: Optional[str] = None) -> List[ReferencedEntity]:
        preceding_entities = []
        for sent_entities in recent_ents_per_sent:
            for preceding_entity in sent_entities.values():
                matching_gender = gender and (preceding_entity.gender == gender or gender == Gender.UNKNOWN)
                matching_type = typ and typ in preceding_entity.types
                if matching_gender or matching_type:
                    preceding_entities.append(preceding_entity)
        return preceding_entities

    def get_clusters(self, article: Article, doc: Optional[Doc] = None) -> List[CorefCluster]:
        if not article.entity_mentions:
            return []

        if doc is None:
            doc = self.model(article.text)
        clusters = defaultdict(list)
        sorted_entity_mentions = sorted(article.entity_mentions.items())
        mention_idx = 0
        recent_ents_per_sent = []
        self.sent_start_idxs = []
        prev_tok = None
        tok_idx = 0
        seen_types = set()
        direct_speeches = get_direct_speeches(article, doc)
        paragraphs = get_paragraphs(article)
        self.type_aliases = dict()

        for sent in doc.sents:

            if len(recent_ents_per_sent) > self.MAX_NUM_SENTS != -1:
                self.sent_start_idxs.pop(0)
                recent_ents_per_sent.pop(0)
            recent_ents_per_sent.append(dict())
            self.sent_start_idxs.append(OffsetConverter.get_token_idx(sent.start_char, doc))

            for tok in sent:
                direct_speech = get_containing_direct_speech(tok.idx, direct_speeches)

                # Add already linked entity at current index
                if mention_idx < len(sorted_entity_mentions) and tok.idx >= sorted_entity_mentions[mention_idx][0][0]:
                    span, entity_mention = sorted_entity_mentions[mention_idx]
                    end_idx = OffsetConverter.get_token_idx(span[1], doc)
                    entity_id = entity_mention.entity_id
                    gender = self.entity_db.get_gender(entity_id)
                    deps = [tok.dep_ for tok in OffsetConverter.get_tokens_in_span(span, doc)]

                    types = set()
                    if entity_id in self.type_aliases:
                        types = self.type_aliases[entity_id]
                    elif self.entity_db.has_coreference_types(entity_id):
                        for type_id in self.entity_db.get_coreference_types(entity_id):
                            type_entity_aliases = self.entity_db.get_entity_aliases(type_id)
                            for alias in type_entity_aliases:
                                alias_list = alias.lower().split("/")
                                types.update(alias_list)
                        self.type_aliases[entity_id] = types
                    seen_types.update(types)

                    referenced_entity = ReferencedEntity(span, entity_id, gender, types, deps, direct_speech)
                    recent_ents_per_sent[-1][(tok_idx, end_idx)] = referenced_entity
                    if span[0] == 0:
                        self.title_entity = referenced_entity
                    mention_idx += 1
                    clusters[entity_id].append(span)

                referenced_entity = None
                span = None

                # Find pronoun coreference
                if PronounFinder.is_pronoun(tok.text):
                    span = tok.idx, tok.idx + len(tok.text)
                    p_text = article.text[span[0]:span[1]].lower()
                    p_gender = PronounFinder.pronoun_genders[p_text]

                    # Don't add "it" to coreference cluster if it does not refer to an object
                    problematic_pronoun = False
                    if p_text == "it":
                        sent = OffsetConverter.get_sentence(span[0], doc)
                        conll_string = DependencyConllExtractor.to_conll_7(sent)
                        dep_graph = EnhancedDependencyGraph(conll_string)
                        it_idx = OffsetConverter.get_token_idx_in_sent(span[0], doc) + 1
                        if dep_graph.is_problematic_it(it_idx):
                            problematic_pronoun = True

                    # Find referenced entity
                    if not problematic_pronoun and (p_gender != Gender.UNKNOWN or
                                                    PronounFinder.is_first_person_singular(tok.text)):
                        # TODO: Consider linking the article entity for all first subject in paragraph pronouns
                        neutral_paragraph_subj = is_first_subj_in_paragraph(tok, paragraphs, doc) and \
                                p_gender == Gender.NEUTRAL
                        preceding_entities = self.get_preceding_entities(recent_ents_per_sent, gender=p_gender)
                        referenced_entity = self.get_referenced_entity(span, preceding_entities, tok.text, doc,
                                                                       max_distance=200, direct_speech=direct_speech,
                                                                       neutral_paragraph_subject=neutral_paragraph_subj)

                # Find "the <type>" coreference
                # TODO only works for single word types right now
                elif tok.text in seen_types and prev_tok and prev_tok.text.lower() in self.COREF_PREFIXES:
                    span = prev_tok.idx, tok.idx + len(tok.text)
                    typ = tok.text.lower()
                    preceding_entities = self.get_preceding_entities(recent_ents_per_sent, typ=typ)
                    referenced_entity = self.get_referenced_entity(span, preceding_entities, tok.text, doc,
                                                                   max_distance=300, type_reference=True,
                                                                   direct_speech=direct_speech)

                # Add coreference to cluster and to preceding entities
                if referenced_entity:
                    # Add coreference to preceding entities under linked entity id
                    deps = [tok.dep_ for tok in OffsetConverter.get_tokens_in_span(span, doc)]
                    new_referenced_entity = ReferencedEntity(span, referenced_entity.entity_id,
                                                             referenced_entity.gender, referenced_entity.types, deps,
                                                             direct_speech)
                    recent_ents_per_sent[-1][(tok_idx, tok_idx)] = new_referenced_entity
                    # Add coreference to coreference cluster
                    clusters[referenced_entity.entity_id].append(span)

                prev_tok = tok
                tok_idx += 1

        coref_clusters = []
        for entity_id, cluster in clusters.items():
            coref_cluster = CorefCluster(cluster[0], cluster, entity_id)
            coref_clusters.append(coref_cluster)
        return coref_clusters
