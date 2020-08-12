from typing import Optional

import spacy
from spacy.tokens import Doc
from spacy.language import Language

from src.wikipedia_article import WikipediaArticle
from src import settings


class CoreferenceGroundtruthGenerator:
    pronouns = {"i", "my", "me", "you", "your", "he", "his", "him", "she", "her", "it", "its", "us", "our",
                "they", "their", "them"}

    def __init__(self,
                 model: Optional[Language] = None):
        if model is None:
            self.model = spacy.load(settings.LARGE_MODEL_NAME)
        else:
            self.model = model

    def find_pronouns(self, doc: Doc):
        pronouns = set()
        for tok in doc:
            if tok.text.lower() in self.pronouns and not tok.text.isupper():  # do not match "US"
                span = (tok.idx, tok.idx + len(tok))
                pronouns.add(span)
        return pronouns

    def get_groundtruth(self, article: WikipediaArticle, doc: Doc = None):
        if doc is None:
            doc = self.model(article.text)
        pronouns = self.find_pronouns(doc)
        referenced_entities = dict()
        entity_to_pronouns = dict()
        pronoun_ground_truth = {((span[0], span[1]), entity_id) for span, entity_id in article.labels
                                if (span[0], span[1]) in pronouns}
        for pronoun_span, entity_id in pronoun_ground_truth:
            if entity_id not in entity_to_pronouns:
                entity_to_pronouns[entity_id] = []
            entity_to_pronouns[entity_id].append(pronoun_span)

        for span, entity_id in article.labels:
            span = (span[0], span[1])
            if span in pronouns:
                referenced_entities[span] = set()

        for span, entity_id in article.labels:
            span = (span[0], span[1])
            if span not in referenced_entities and entity_id in entity_to_pronouns:
                for pronoun_span in entity_to_pronouns[entity_id]:
                    # Only add span as potential referenced span, if it precedes the pronoun in the text
                    if span[0] < pronoun_span[0]:
                        referenced_entities[pronoun_span].add(span)

        return referenced_entities
