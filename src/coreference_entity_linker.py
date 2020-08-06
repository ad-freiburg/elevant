from typing import Optional

import spacy
import neuralcoref
from spacy.tokens import Doc
from spacy.language import Language

from src import settings
from src.wikipedia_article import WikipediaArticle
from src.entity_mention import EntityMention


class CoreferenceEntityLinker:
    IDENTIFIER = "COREFERENCE"

    def __init__(self, model: Optional[Language] = None):
        if model is None:
            self.model = spacy.load(settings.LARGE_MODEL_NAME)
        else:
            self.model = model
        neuralcoref.add_to_pipe(self.model)

    def link_entities(self, article: WikipediaArticle, doc: Optional[Doc] = None):
        if doc is None:
            doc = self.model(article.text)
        new_entity_mentions = []
        if not doc._.coref_clusters:
            article.add_entity_mentions([])
            return
        for coreference_cluster in doc._.coref_clusters:
            main = coreference_cluster.main
            main_span = (main.start_char, main.end_char)
            # print("Coreference found at (%d, %d): %s" %
            #       (main_span[0], main_span[1], article.text[main_span[0]:main_span[1]]))
            entity_id = article.get_overlapping_entity(main_span)
            if entity_id:
                # print("Main span entity: %s" % entity_id)
                for mention in coreference_cluster.mentions:
                    mention_span = (mention.start_char, mention.end_char)
                    if not article.get_overlapping_entity(mention_span):
                        entity_mention = EntityMention(mention_span, recognized_by=self.IDENTIFIER, entity_id=entity_id,
                                                       linked_by=self.IDENTIFIER)
                        new_entity_mentions.append(entity_mention)
        article.add_entity_mentions(new_entity_mentions)
