from typing import Optional

import spacy
from spacy.language import Language

from src.pronoun_finder import PronounFinder
from src.wikipedia_article import WikipediaArticle
from src import settings


def is_coreference(text):
    return PronounFinder.is_pronoun(text) or (text.lower().startswith("the ") and len(text) > 4 and text[4].islower())


class CoreferenceGroundtruthGenerator:
    def __init__(self,
                 model: Optional[Language] = None):
        if model is None:
            self.model = spacy.load(settings.LARGE_MODEL_NAME)
        else:
            self.model = model

    @staticmethod
    def get_groundtruth(article: WikipediaArticle):
        if not article.labels:
            return {}

        referenced_entities = {}
        entity_to_pronouns = {}
        pronoun_ground_truth = []
        for span, entity_id in article.labels:
            text = article.text[span[0]:span[1]]
            if is_coreference(text):
                pronoun_ground_truth.append(((span[0], span[1]), entity_id))
        for pronoun_span, entity_id in pronoun_ground_truth:
            if entity_id not in entity_to_pronouns:
                entity_to_pronouns[entity_id] = []
            entity_to_pronouns[entity_id].append(pronoun_span)

        for span, entity_id in article.labels:
            span = (span[0], span[1])
            text = article.text[span[0]:span[1]]
            if is_coreference(text):
                referenced_entities[span] = set()

        for span, entity_id in article.labels:
            span = (span[0], span[1])
            if span not in referenced_entities and entity_id in entity_to_pronouns:
                for pronoun_span in entity_to_pronouns[entity_id]:
                    # Only add span as potential referenced span, if it precedes the pronoun in the text
                    if span[0] < pronoun_span[0]:
                        referenced_entities[pronoun_span].add(span)

        return referenced_entities
