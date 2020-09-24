from typing import Optional, Tuple, List, Set
from spacy.tokens import Doc, Token, Span
from spacy.language import Language

import spacy
from collections import defaultdict

from src.abstract_coref_linker import AbstractCorefLinker
from src.coref_cluster import CorefCluster
from src.custom_sentencizer import CustomSentencizer
from src.dependency_conll_extractor import DependencyConllExtractor
from src.dependency_graph import EnhancedDependencyGraph
from src.entity_database import EntityDatabase
from src.gender import Gender
from src.offset_converter import OffsetConverter
from src.pronoun_finder import PronounFinder
from src.wikipedia_article import WikipediaArticle
from src import settings


class ReferencedEntity:
    def __init__(self, span: Tuple[int, int], entity_id: str, gender: Gender, types: Set[str], deps: List[str]):
        self.span = span
        self.entity_id = entity_id
        self.gender = gender
        self.types = types
        self.deps = deps


class EntityCorefLinker(AbstractCorefLinker):
    MAX_NUM_SENTS = -1
    COREF_PREFIXES = ("the", "that", "this")

    def __init__(self, entity_db: EntityDatabase, model: Optional[Language] = None):
        if model is None:
            self.model = spacy.load(settings.LARGE_MODEL_NAME)
            self.model.add_pipe(CustomSentencizer.set_custom_boundaries, before="parser")
        else:
            self.model = model
        self.entity_db = entity_db
        self.sent_start_idxs = None
        if not self.entity_db.is_gender_loaded():
            print("Load gender mapping...")
            self.entity_db.load_gender()
        if not self.entity_db.is_types_loaded():
            print("Load types mapping...")
            self.entity_db.load_types()
        if self.entity_db.size_entities() == 0:
            print("Load entities...")
            self.entity_db.load_entities_big()

    def get_referenced_entity(self, span, preceding_entities, tok_text, doc=None, max_distance=None,
                              type_reference=False):
        referenced_entity = None
        for i, preceding_entity in enumerate(reversed(preceding_entities)):
            pre_span = preceding_entity.span
            if pre_span[1] + max_distance < span[0]:
                break
            if i == 0:
                referenced_entity = preceding_entity
            if "nsubj" in preceding_entity.deps or "nsubjpass" in preceding_entity.deps:
                referenced_entity = preceding_entity
                break
        return referenced_entity

    @staticmethod
    def get_preceding_entities(recent_ents_per_sent, gender, typ):
        preceding_entities = []
        for sent_entities in recent_ents_per_sent:
            for preceding_entity in sent_entities.values():
                if (gender and preceding_entity.gender == gender) or \
                        (not gender and typ and typ in preceding_entity.types):
                    preceding_entities.append(preceding_entity)
        return preceding_entities

    def get_clusters(self, article: WikipediaArticle, doc: Optional[Doc] = None):
        if not article.entity_mentions:
            return []

        doc = self.model(article.text)

        clusters = defaultdict(list)
        sorted_entity_mentions = sorted(article.entity_mentions.items())
        mention_idx = 0
        recent_ents_per_sent = []
        self.sent_start_idxs = []
        prev_tok = None
        tok_idx = 0
        seen_types = set()

        for sent in doc.sents:

            if len(recent_ents_per_sent) > self.MAX_NUM_SENTS != -1:
                self.sent_start_idxs.pop(0)
                recent_ents_per_sent.pop(0)
            recent_ents_per_sent.append(dict())
            self.sent_start_idxs.append(OffsetConverter.get_token_idx(sent.start_char, doc))

            for tok in sent:
                # Add already linked entity at current index
                if mention_idx < len(sorted_entity_mentions) and tok.idx >= sorted_entity_mentions[mention_idx][0][0]:
                    span, entity_mention = sorted_entity_mentions[mention_idx]
                    end_idx = OffsetConverter.get_token_idx(span[1], doc)
                    entity_id = entity_mention.entity_id
                    gender = self.entity_db.get_gender(entity_id)
                    deps = [tok.dep_ for tok in OffsetConverter.get_tokens_in_span(span, doc)]

                    types = set()
                    if self.entity_db.has_types(entity_id):
                        for type_id in self.entity_db.get_types(entity_id):
                            if self.entity_db.contains_entity(type_id):
                                type_entity = self.entity_db.get_entity(type_id)
                                names = type_entity.synonyms + [type_entity.name]
                                for name in names:
                                    types.add(name.lower())
                        seen_types.update(types)
                    referenced_entity = ReferencedEntity(span, entity_id, gender, types, deps)
                    recent_ents_per_sent[-1][(tok_idx, end_idx)] = referenced_entity
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
                    if not problematic_pronoun and p_gender != Gender.UNKNOWN:
                        preceding_entities = self.get_preceding_entities(recent_ents_per_sent, p_gender, None)
                        referenced_entity = self.get_referenced_entity(span, preceding_entities, tok.text, doc,
                                                                       max_distance=200)

                # Find "the <type>" coreference
                # TODO only works for single word types right now
                elif tok.text.lower() in seen_types and prev_tok and prev_tok.text.lower() in self.COREF_PREFIXES:
                    span = prev_tok.idx, tok.idx + len(tok.text)
                    typ = tok.text.lower()
                    preceding_entities = self.get_preceding_entities(recent_ents_per_sent, None, typ)
                    referenced_entity = self.get_referenced_entity(span, preceding_entities, tok.text, doc,
                                                                   max_distance=300, type_reference=True)

                # Add coreference to cluster and to preceding entities
                if referenced_entity:
                    # Add coreference to preceding entities under linked entity id
                    deps = [tok.dep_ for tok in OffsetConverter.get_tokens_in_span(span, doc)]
                    new_referenced_entity = ReferencedEntity(span, referenced_entity.entity_id,
                                                             referenced_entity.gender, referenced_entity.types, deps)
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
