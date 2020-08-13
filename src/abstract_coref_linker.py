from typing import Optional, Tuple

import abc
from spacy.tokens import Doc
from src.coreference_groundtruth_generator import CoreferenceGroundtruthGenerator
from src.wikipedia_article import WikipediaArticle
from src.entity_mention import EntityMention


class AbstractCorefLinker(abc.ABC):
    IDENTIFIER = "COREFERENCE"

    @abc.abstractmethod
    def get_clusters(self, article: WikipediaArticle, doc: Optional[Doc] = None):
        raise NotImplementedError()

    def link_entities(self,
                      article: WikipediaArticle,
                      doc: Optional[Doc] = None,
                      only_pronouns: Optional[bool] = False,
                      evaluation_span: Tuple[int, int] = None):
        coref_clusters = self.get_clusters(article, doc)
        new_entity_mentions = []
        if not coref_clusters:
            article.add_entity_mentions([])
            return
        for coreference_cluster in coref_clusters:
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

    def predict(self,
                article: WikipediaArticle,
                doc: Optional[Doc] = None,
                only_pronouns: Optional[bool] = False,
                evaluation_span: Tuple[int, int] = None):
        coref_clusters = self.get_clusters(article, doc)
        predictions = dict()
        if not coref_clusters:
            return predictions
        for coreference_cluster in coref_clusters:
            main = coreference_cluster.main
            main_span = (main.start_char, main.end_char)

            if evaluation_span:
                new_main_span = self.get_first_reference_in_span(coreference_cluster.mentions, evaluation_span)
                main_span = new_main_span if new_main_span else main_span

            for mention in coreference_cluster.mentions:
                mention_span = (mention.start_char, mention.end_char)
                if mention_span == main_span:
                    continue
                mention_text = article.text[mention_span[0]:mention_span[1]]
                if only_pronouns and mention_text.lower() not in CoreferenceGroundtruthGenerator.pronouns:
                    continue
                predictions[mention_span] = main_span
        return predictions

    @staticmethod
    def get_first_reference_in_span(mentions, span: Tuple[int, int]) -> Tuple[int, int]:
        for mention in mentions:
            if mention.start_char >= span[0] and mention.end_char <= span[1]:
                return mention.start_char, mention.end_char
