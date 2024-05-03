from typing import Optional, Tuple, List

import abc
from spacy.tokens import Doc
from elevant.utils.pronoun_finder import PronounFinder
from elevant.models.article import Article
from elevant.models.entity_mention import EntityMention
from elevant.evaluation.mention_type import is_coreference


class AbstractCorefLinker(abc.ABC):
    IDENTIFIER = "COREFERENCE"

    @abc.abstractmethod
    def get_clusters(self, article: Article, doc: Optional[Doc] = None):
        raise NotImplementedError()

    def link_entities(self,
                      article: Article,
                      doc: Optional[Doc] = None,
                      only_pronouns: Optional[bool] = False,
                      evaluation_span: Optional[Tuple[int, int]] = None,
                      verbose: Optional[bool] = False):
        coref_clusters = self.get_clusters(article, doc)
        if verbose:
            self.print_clusters(coref_clusters, article.text)
        new_entity_mentions = []
        if not coref_clusters:
            article.add_entity_mentions([])
            return
        for coreference_cluster in coref_clusters:
            main = coreference_cluster.main
            main_span = (main[0], main[1])

            if evaluation_span:
                new_main_span = self.get_first_reference_in_span(coreference_cluster.mentions, evaluation_span)
                main_span = new_main_span if new_main_span else main_span

            main_mention = article.get_overlapping_entity(main_span)

            if main_mention:
                entity_id = main_mention.entity_id
                for mention in coreference_cluster.mentions:
                    mention_span = (mention[0], mention[1])
                    mention_text = article.text[mention_span[0]:mention_span[1]]
                    if only_pronouns and not PronounFinder.is_pronoun(mention_text):
                        continue
                    if not article.get_overlapping_entity(mention_span):
                        entity_mention = EntityMention(mention_span, recognized_by=self.IDENTIFIER, entity_id=entity_id,
                                                       linked_by=self.IDENTIFIER, candidates={entity_id},
                                                       referenced_span=main_mention.span)
                        new_entity_mentions.append(entity_mention)
        article.add_entity_mentions(new_entity_mentions)

    def predict(self,
                article: Article,
                doc: Optional[Doc] = None,
                only_pronouns: Optional[bool] = False,
                evaluation_span: Optional[Tuple[int, int]] = None,
                verbose: Optional[bool] = False):
        coref_clusters = self.get_clusters(article, doc)
        if verbose:
            self.print_clusters(coref_clusters, article.text)
        predictions = dict()
        if not coref_clusters:
            return predictions
        for coreference_cluster in coref_clusters:
            main = coreference_cluster.main
            main_span = (main[0], main[1])

            if evaluation_span:
                new_main_span = self.get_first_reference_in_span(coreference_cluster.mentions, evaluation_span)
                main_span = new_main_span if new_main_span else main_span

            for mention in coreference_cluster.mentions:
                mention_span = (mention[0], mention[1])
                if mention_span == main_span:
                    continue
                mention_text = article.text[mention_span[0]:mention_span[1]]
                if only_pronouns and not PronounFinder.is_pronoun(mention_text):
                    continue
                if not article.get_overlapping_entity(mention_span) and is_coreference(mention_text):
                    predictions[mention_span] = main_span
        return predictions

    @staticmethod
    def get_first_reference_in_span(mentions: List[Tuple[int, int]], span: Tuple[int, int]) -> Tuple[int, int]:
        for mention in mentions:
            # Look for overlapping spans
            if span[0] <= mention[0] <= span[1] or span[0] <= mention[1] <= span[1]:
                return mention[0], mention[1]

    @staticmethod
    def print_clusters(clusters, text):
        print()
        print("Predicted coreference clusters:")
        for i, cluster in enumerate(clusters):
            for j, span in enumerate(cluster.mentions):
                end = " | " if j < len(cluster.mentions) - 1 else "\n"
                text_span = text[span[0]:span[1]].replace("\n", "<br>")
                print("(%d,%d) [%s]" % (span[0], span[1], text_span), end=end)
        print()
