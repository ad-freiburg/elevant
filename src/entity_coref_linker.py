from typing import Optional
from spacy.tokens import Doc
from spacy.language import Language

import spacy

from src.abstract_coref_linker import AbstractCorefLinker
from src.coref_cluster import CorefCluster
from src.entity_database import EntityDatabase
from src.gender import Gender
from src.pronoun_finder import PronounFinder
from src.wikipedia_article import WikipediaArticle
from src import settings


class EntityCorefLinker(AbstractCorefLinker):
    def __init__(self, entity_db: EntityDatabase, model: Optional[Language] = None):
        if model is None:
            self.model = spacy.load(settings.LARGE_MODEL_NAME)
        else:
            self.model = model
        self.entity_db = entity_db

    def get_clusters(self, article: WikipediaArticle, doc: Optional[Doc] = None):
        if doc is None:
            doc = self.model(article.text)

        pronoun_spans = sorted(PronounFinder.find_pronouns(doc))
        pronoun_idx = 0
        preceding_entity = [None for _ in range(len(Gender))]
        clusters = {}

        if not article.entity_mentions:
            return []

        for span, entity_mention in sorted(article.entity_mentions.items()):
            if pronoun_idx < len(pronoun_spans) and span[0] > pronoun_spans[pronoun_idx][0]:
                p_span = pronoun_spans[pronoun_idx]
                p_text = article.text[p_span[0]:p_span[1]].lower()
                p_gender = PronounFinder.pronouns[p_text]
                referenced_entity = preceding_entity[p_gender.value]
                if referenced_entity:
                    clusters[referenced_entity].append(p_span)
                pronoun_idx += 1

            entity_id = entity_mention.entity_id
            gender = self.entity_db.get_gender(entity_id)
            preceding_entity[gender.value] = entity_id
            if entity_id not in clusters:
                clusters[entity_id] = []
            clusters[entity_id].append(span)

        coref_clusters = []
        for entity_id, cluster in clusters.items():
            coref_cluster = CorefCluster(cluster[0], cluster, entity_id)
            coref_clusters.append(coref_cluster)
        return coref_clusters
