from typing import Optional, Tuple

import spacy
import neuralcoref
from spacy.tokens import Doc
from spacy.language import Language

from src import settings
from src.coreference_groundtruth_generator import CoreferenceGroundtruthGenerator
from src.wikipedia_article import WikipediaArticle
from src.entity_mention import EntityMention


class CoreferenceEntityLinker:
    IDENTIFIER = "COREFERENCE"

    def __init__(self,
                 model: Optional[Language] = None):
        if model is None:
            self.model = spacy.load(settings.LARGE_MODEL_NAME)
        else:
            self.model = model
        neuralcoref.add_to_pipe(self.model, max_dist=50, max_dist_match=100)

    def link_entities(self,
                      article: WikipediaArticle,
                      doc: Optional[Doc] = None,
                      only_pronouns: Optional[bool] = False,
                      evaluation_span: Tuple[int, int] = None):
        if doc is None:
            doc = self.model(article.text)
        new_entity_mentions = []
        if not doc._.coref_clusters:
            article.add_entity_mentions([])
            return
        for coreference_cluster in doc._.coref_clusters:
            main = coreference_cluster.main
            main_span = (main.start_char, main.end_char)

            if evaluation_span:
                new_main_span = self.get_first_reference_in_span(coreference_cluster.mentions, evaluation_span)
                main_span = new_main_span if new_main_span else main_span

            main_mention = article.get_overlapping_entity(main_span)

            if main_mention:
                entity_id = main_mention.entity_id
                for mention in coreference_cluster.mentions:
                    mention_span = (mention.start_char, mention.end_char)
                    mention_text = article.text[mention_span[0]:mention_span[1]]
                    if only_pronouns and mention_text.lower() not in CoreferenceGroundtruthGenerator.pronouns:
                        continue
                    if not article.get_overlapping_entity(mention_span):
                        entity_mention = EntityMention(mention_span, recognized_by=self.IDENTIFIER, entity_id=entity_id,
                                                       linked_by=self.IDENTIFIER, referenced_span=main_mention.span)
                        new_entity_mentions.append(entity_mention)
        article.add_entity_mentions(new_entity_mentions)

    @staticmethod
    def get_first_reference_in_span(mentions, span: Tuple[int, int]) -> Tuple[int, int]:
        for mention in mentions:
            if mention.start_char >= span[0]:
                return mention.start_char, mention.end_char
