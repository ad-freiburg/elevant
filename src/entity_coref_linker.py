from typing import Optional, Tuple, List
from spacy.tokens import Doc, Token
from spacy.language import Language

import spacy

from src.abstract_coref_linker import AbstractCorefLinker
from src.coref_cluster import CorefCluster
from src.entity_database import EntityDatabase
from src.entity_mention import EntityMention
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

    def get_clusters(self, article: WikipediaArticle, doc: Optional[Doc] = None):
        if doc is None:
            doc = self.model(article.text)

        pronoun_spans = sorted(PronounFinder.find_pronouns(doc))
        pronoun_idx = 0
        preceding_entities = [[] for _ in range(len(Gender))]
        clusters = {}

        if not article.entity_mentions:
            return []

        all_entity_mentions = article.entity_mentions
        for span, entity_mention in sorted(all_entity_mentions.items()):
            if pronoun_idx < len(pronoun_spans) and span[0] > pronoun_spans[pronoun_idx][0]:
                p_span = pronoun_spans[pronoun_idx]
                p_text = article.text[p_span[0]:p_span[1]].lower()
                p_gender = PronounFinder.pronoun_genders[p_text]
                referenced_entity = None
                # print("Pronoun span: (%d,%d)[%s]" % (p_span[0], p_span[1], p_text))
                for i, preceding_entity in enumerate(reversed(preceding_entities[p_gender.value])):
                    pre_span = preceding_entity.span
                    # print("Preceding entity: (%d,%d)[%s]" % (pre_span[0], pre_span[1], article.text[pre_span[0]:pre_span[1]]))
                    if pre_span[1] + 200 < p_span[0]:
                        break
                    if i == 0:
                        referenced_entity = preceding_entity
                        # print("FIRST PRECEDING ENTITY")
                    if "nsubj" in preceding_entity.deps or "nsubjpass" in preceding_entity.deps:
                        referenced_entity = preceding_entity
                        # print("SUBJECT!")
                        break

                if referenced_entity:
                    # Add pronoun to preceding entities under linked entity id
                    deps = [tok.dep_ for tok in get_tokens_in_span(p_span, doc)]
                    new_referenced_entity = ReferencedEntity(p_span, referenced_entity.entity_id, referenced_entity.gender, deps)
                    preceding_entities[referenced_entity.gender.value].append(new_referenced_entity)
                    # Add pronoun to coreference cluster
                    clusters[referenced_entity.entity_id].append(p_span)
                pronoun_idx += 1

            entity_id = entity_mention.entity_id
            gender = self.entity_db.get_gender(entity_id)
            deps = [tok.dep_ for tok in get_tokens_in_span(span, doc)]
            ref_entity = ReferencedEntity(span, entity_id, gender, deps)
            preceding_entities[gender.value].append(ref_entity)

            # print("Add pre entity under %s: (%d,%d)[%s:%s], deps: %s" % (gender.value, span[0], span[1], entity_id, article.text[span[0]:span[1]], deps))
            if entity_id not in clusters:
                clusters[entity_id] = []
            clusters[entity_id].append(span)

        coref_clusters = []
        for entity_id, cluster in clusters.items():
            coref_cluster = CorefCluster(cluster[0], cluster, entity_id)
            coref_clusters.append(coref_cluster)
        return coref_clusters
