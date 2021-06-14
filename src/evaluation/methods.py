from typing import Tuple, List

from src.evaluation.case import Case
from src.evaluation.groundtruth_label import EntityType
from src.linkers.abstract_coref_linker import AbstractCorefLinker
from src.models.entity_database import EntityDatabase
from src.models.wikidata_entity import WikidataEntity
from src.models.wikipedia_article import WikipediaArticle


def get_evaluation_cases(article: WikipediaArticle,
                         ground_truth,
                         coref_ground_truth,
                         entity_db: EntityDatabase) -> List[Case]:
    predictions = article.entity_mentions
    expanded_prediction_spans = {word_boundary(span, article.text): prediction
                                 for span, prediction in predictions.items()}
    all_predictions = predictions.copy()
    all_predictions.update(expanded_prediction_spans)
    evaluation_span = article.evaluation_span

    ground_truth_spans = set()
    for gt_label in article.labels:
        ground_truth_spans.add(gt_label.span)
        ground_truth_spans.add(word_boundary(gt_label.span, article.text))

    cases = []

    label_dict = dict()
    for gt_label in article.labels:
        label_dict[gt_label.id] = gt_label

    # ground truth cases:
    for gt_label in sorted(article.labels):
        span = gt_label.span
        expanded_span = word_boundary(span, article.text)
        text = article.text[span[0]:span[1]]
        detected = span in all_predictions or expanded_span in all_predictions
        predicted_mention = None
        if detected:
            predicted_mention = all_predictions[span] if span in all_predictions else all_predictions[expanded_span]
            candidates = set()
            for cand_id in predicted_mention.candidates:
                if entity_db.contains_entity(cand_id):
                    candidates.add(WikidataEntity(entity_db.get_entity(cand_id).name, 0, cand_id, []))
            predicted_by = predicted_mention.linked_by
            predicted_entity_id = predicted_mention.entity_id
            predicted_entity_name = entity_db.get_entity(predicted_entity_id).name \
                if entity_db.contains_entity(predicted_entity_id) else "Unknown"

            entity_type = EntityType.OTHER
            if entity_db.is_quantity(predicted_entity_id):
                entity_type = EntityType.QUANTITY
            if entity_db.is_datetime(predicted_entity_id):
                entity_type = EntityType.DATETIME

            predicted_entity = WikidataEntity(predicted_entity_name, 0, predicted_mention.entity_id, [],
                                              type=entity_type)
            contained = predicted_mention.contained
        else:
            predicted_by = None
            predicted_entity = None
            candidates = set()
            contained = None

        referenced_span = None
        is_true_coref = span in coref_ground_truth
        correct_span_referenced = False
        if detected and predicted_by == AbstractCorefLinker.IDENTIFIER:
            referenced_span = predicted_mention.referenced_span
            if is_true_coref:
                for poss_ref_span in coref_ground_truth[span]:
                    # Do not require a perfect match of the spans but look for overlaps
                    if poss_ref_span[0] <= referenced_span[1] <= poss_ref_span[1] or \
                            poss_ref_span[0] <= referenced_span[0] <= poss_ref_span[1]:
                        correct_span_referenced = True
                        break

        # Due to our overlapping gt labels, some cases should not count, others should only count a fraction of a case
        if gt_label.parent in label_dict:
            parent = label_dict[gt_label.parent]
            factor = 1 / len(parent.children)
        else:
            factor = 1
        # If gt_label is parent of a child label that was detected, don't count parent label -> factor = 0
        sibling_wrong = False
        if gt_label.children:
            for child_id in gt_label.children:
                child = label_dict[child_id]
                expanded_child_span = word_boundary(child.span, article.text)
                # If parent span = child span, parent factor is only 0 if child entity id matches predicted entity id
                if (child.span in all_predictions or expanded_child_span in all_predictions) and \
                        (expanded_span != expanded_child_span or
                         (predicted_entity and child.entity_id == predicted_entity.entity_id)):
                    factor = 0
                    break
        elif gt_label.parent:
            # If gt_label is child of a parent label that was detected, or if none of the parents children were detected
            # don't count child label -> factor = 0
            parent = label_dict[gt_label.parent]
            expanded_parent_span = word_boundary(parent.span, article.text)
            if (parent.span in all_predictions or expanded_parent_span in all_predictions) and \
                    (expanded_span != expanded_parent_span or
                     (predicted_entity and gt_label.entity_id != predicted_entity.entity_id)):
                factor = 0
            else:
                sibling_detected = False
                for sibling_id in parent.children:
                    sibling = label_dict[sibling_id]
                    expanded_sibling_span = word_boundary(sibling.span, article.text)
                    if sibling.span in all_predictions or expanded_sibling_span in all_predictions:
                        sibling_detected = True
                        pred_entity_id = all_predictions[sibling.span].entity_id if sibling.span in all_predictions \
                            else all_predictions[expanded_sibling_span].entity_id
                        if pred_entity_id != sibling.entity_id:
                            sibling_wrong = True
                            break
                if not sibling_detected:
                    factor = 0

        case = Case(span, text, gt_label, detected, predicted_entity, candidates, predicted_by,
                    contained=contained,
                    is_true_coref=is_true_coref,
                    correct_span_referenced=correct_span_referenced,
                    referenced_span=referenced_span,
                    factor=factor,
                    all_siblings_correct=not sibling_wrong)
        cases.append(case)

    # predicted cases (potential false detections):
    for span in sorted(predictions):
        expanded_span = word_boundary(span, article.text)
        predicted_mention = predictions[span]

        candidates = set()
        for cand_id in predicted_mention.candidates:
            if entity_db.contains_entity(cand_id):
                candidates.add(WikidataEntity(entity_db.get_entity(cand_id).name, 0, cand_id, []))

        predicted_entity_id = predicted_mention.entity_id
        predicted_entity_name = entity_db.get_entity(predicted_entity_id).name \
            if entity_db.contains_entity(predicted_entity_id) else "Unknown"
        predicted_entity = WikidataEntity(predicted_entity_name, 0, predicted_mention.entity_id, [])

        if (span not in ground_truth_spans and expanded_span not in ground_truth_spans) and \
                predicted_entity_id is not None and span[0] >= evaluation_span[0] and span[1] <= evaluation_span[1]:
            text = article.text[span[0]:span[1]]
            predicted_by = predicted_mention.linked_by
            contained = predicted_mention.contained
            case = Case(span, text, None, True, predicted_entity, contained=contained, candidates=candidates,
                        predicted_by=predicted_by, referenced_span=predicted_mention.referenced_span, factor=1)
            cases.append(case)

    return sorted(cases)


def word_boundary(span: Tuple[int, int], text: str) -> Tuple[int, int]:
    """
    Given a span and the article text, expand the span to match the word
    boundaries to the left and right.
    Word boundaries are indicated by spaces and non-alphanumeric characters
    other than "'\"_".
    >>> word_boundary((0, 6), "Albert's birthplace is Ulm.")
    (0, 8)
    >>> word_boundary((1, 19), '"Hearts and Flowers" is a song.')
    (0, 20)
    >>> word_boundary((0, 6), "Soviet-backed government.")
    (0, 6)
    """
    extended_span = [span[0], span[1]]
    while extended_span[0] > 0 and (text[extended_span[0] - 1].isalnum() or text[extended_span[0] - 1] in "'\"_"):
        # Extend span to the left until it reaches a whitespace
        extended_span[0] -= 1
    while extended_span[1] < len(text) - 1 and (text[extended_span[1]].isalnum()
                                                or text[extended_span[1]] in "'\"_"):
        # Extend span to the right until it reaches whitespace or punctuation except for those noted
        extended_span[1] += 1
    if text[extended_span[0]] == '"' and '"' not in text[extended_span[0] + 1:extended_span[1]]:
        # Avoid expanding spans in cases like 'MetalStorm wrote: "Gore Metal features ...'
        extended_span[0] += 1
    return extended_span[0], extended_span[1]
