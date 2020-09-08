from typing import Optional, Tuple, List
from spacy.tokens import Doc, Token, Span
from spacy.language import Language

import spacy
from collections import defaultdict

from src.abstract_coref_linker import AbstractCorefLinker
from src.coref_cluster import CorefCluster
from src.dependency_conll_extractor import DependencyConllExtractor
from src.dependency_graph import EnhancedDependencyGraph
from src.entity_database import EntityDatabase
from src.gender import Gender
from src.pronoun_finder import PronounFinder
from src.wikipedia_article import WikipediaArticle
from src import settings


class ReferencedEntity:
    def __init__(self, span: Tuple[int, int], entity_id: str, gender: Gender, deps: List[str]):
        self.span = span
        self.entity_id = entity_id
        self.gender = gender
        self.deps = deps


def get_tokens_in_span(span: Tuple[int, int], doc: Doc) -> List[Token]:
    tokens = []
    for token in doc:
        if token.idx >= span[0] and token.idx + len(token.text) <= span[1]:
            tokens.append(token)
    return tokens


def get_sentence(offset: int, doc: Doc) -> Span:
    for i, sent in enumerate(doc.sents):
        if sent.end_char >= offset:
            return sent


def get_token_idx_in_sent(offset: int, doc: Doc) -> int:
    for i, sent in enumerate(doc.sents):
        for j, tok in enumerate(sent):
            if tok.idx >= offset:
                return j


class EntityCorefLinker(AbstractCorefLinker):
    def __init__(self, entity_db: EntityDatabase, model: Optional[Language] = None):
        if model is None:
            self.model = spacy.load(settings.LARGE_MODEL_NAME)
        else:
            self.model = model
        self.entity_db = entity_db
        if not self.entity_db.is_gender_loaded():
            print("Load gender mapping...")
            self.entity_db.load_gender()
        if not self.entity_db.is_types_loaded():
            print("Load types mapping...")
            self.entity_db.load_types()
        if self.entity_db.size_entities() == 0:
            print("Load entities...")
            self.entity_db.load_entities_big()

    @staticmethod
    def get_referenced_entity(span, preceding_entities, max_distance=200):
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

    def get_clusters(self, article: WikipediaArticle, doc: Optional[Doc] = None):
        if not article.entity_mentions:
            return []

        if doc is None:
            doc = self.model(article.text)

        preceding_entities_by_gender = defaultdict(list)
        preceding_entities_by_type = defaultdict(list)
        clusters = defaultdict(list)
        sorted_entity_mentions = sorted(article.entity_mentions.items())
        mention_idx = 0
        prev_tok = None
        for tok in doc:
            # Find preceding, already linked entities
            if mention_idx < len(sorted_entity_mentions) and tok.idx >= sorted_entity_mentions[mention_idx][0][0]:
                span, entity_mention = sorted_entity_mentions[mention_idx]
                entity_id = entity_mention.entity_id
                gender = self.entity_db.get_gender(entity_id)
                deps = [tok.dep_ for tok in get_tokens_in_span(span, doc)]
                referenced_entity = ReferencedEntity(span, entity_id, gender, deps)
                preceding_entities_by_gender[gender].append(referenced_entity)
                if self.entity_db.has_types(entity_id):
                    for type_id in self.entity_db.get_types(entity_id):
                        if self.entity_db.contains_entity(type_id):
                            type_entity = self.entity_db.get_entity(type_id)
                            names = type_entity.synonyms + [type_entity.name]
                            for name in names:
                                preceding_entities_by_type[name.lower()].append(referenced_entity)
                clusters[entity_id].append(span)
                mention_idx += 1

            # Find pronoun coreference
            elif PronounFinder.is_pronoun(tok.text):
                span = tok.idx, tok.idx + len(tok.text)
                p_text = article.text[span[0]:span[1]].lower()
                p_gender = PronounFinder.pronoun_genders[p_text]

                # Don't add "it" to coreference cluster if it does not refer to an object
                problematic_pronoun = False
                if p_text == "it":
                    sent = get_sentence(span[0], doc)
                    conll_string = DependencyConllExtractor.to_conll_7(sent)
                    dep_graph = EnhancedDependencyGraph(conll_string)
                    it_idx = get_token_idx_in_sent(span[0], doc) + 1
                    if dep_graph.is_problematic_it(it_idx):
                        problematic_pronoun = True

                # Find referenced entity
                if not problematic_pronoun:
                    referenced_entity = self.get_referenced_entity(span, preceding_entities_by_gender[p_gender])

                    # Add coreference to cluster and to preceding entities
                    if referenced_entity:
                        # Add pronoun to preceding entities under linked entity id
                        deps = [tok.dep_ for tok in get_tokens_in_span(span, doc)]
                        new_referenced_entity = ReferencedEntity(span, referenced_entity.entity_id,
                                                                 referenced_entity.gender, deps)
                        preceding_entities_by_gender[referenced_entity.gender].append(new_referenced_entity)
                        # Add pronoun to coreference cluster
                        clusters[referenced_entity.entity_id].append(span)

            # Find "the <type>" coreference
            # TODO only works for single word types right now
            elif tok.text in preceding_entities_by_type and prev_tok and prev_tok.text.lower() == "the":
                span = prev_tok.idx, tok.idx + len(tok.text)
                referenced_entity = self.get_referenced_entity(span, preceding_entities_by_type[tok.text.lower()],
                                                               max_distance=300)
                if referenced_entity:
                    clusters[referenced_entity.entity_id].append(span)
                    deps = [tok.dep_ for tok in get_tokens_in_span(span, doc)]
                    new_referenced_entity = ReferencedEntity(span, referenced_entity.entity_id, Gender.UNKNOWN, deps)
                    preceding_entities_by_type[tok.text.lower()].append(new_referenced_entity)

            prev_tok = tok

        coref_clusters = []
        for entity_id, cluster in clusters.items():
            coref_cluster = CorefCluster(cluster[0], cluster, entity_id)
            coref_clusters.append(coref_cluster)
        return coref_clusters
