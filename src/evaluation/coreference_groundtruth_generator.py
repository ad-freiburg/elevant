from typing import Dict, Tuple, Set

from src.models.article import Article
from src.evaluation.mention_type import is_coreference


class CoreferenceGroundtruthGenerator:
    @staticmethod
    def get_groundtruth(article: Article) -> Dict[Tuple[int, int], Set[Tuple[int, int]]]:
        if not article.labels:
            return {}

        referenced_entities = {}
        entity_to_pronouns = {}
        pronoun_ground_truth = []
        for gt_label in article.labels:
            span = gt_label.span
            entity_id = gt_label.entity_id
            text = article.text[span[0]:span[1]]
            if is_coreference(text):
                pronoun_ground_truth.append(((span[0], span[1]), entity_id))
        for pronoun_span, entity_id in pronoun_ground_truth:
            if entity_id not in entity_to_pronouns:
                entity_to_pronouns[entity_id] = []
            entity_to_pronouns[entity_id].append(pronoun_span)

        for gt_label in article.labels:
            span = gt_label.span
            text = article.text[span[0]:span[1]]
            if is_coreference(text):
                referenced_entities[span] = set()

        for gt_label in article.labels:
            span = gt_label.span
            entity_id = gt_label.entity_id
            if entity_id in entity_to_pronouns:
                for pronoun_span in entity_to_pronouns[entity_id]:
                    # Only add span as potential referenced span, if it precedes the pronoun in the text
                    if span[0] < pronoun_span[0]:
                        referenced_entities[pronoun_span].add(span)

        return referenced_entities
