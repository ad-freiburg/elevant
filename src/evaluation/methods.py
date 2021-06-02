from src.evaluation.case import Case
from src.evaluation.groundtruth_label import EntityType
from src.linkers.abstract_coref_linker import AbstractCorefLinker
from src.models.wikidata_entity import WikidataEntity
from src.models.wikipedia_article import WikipediaArticle


def get_evaluation_cases(article: WikipediaArticle,
                         ground_truth,
                         coref_ground_truth,
                         entity_db):
    predictions = article.entity_mentions
    evaluation_span = article.evaluation_span

    ground_truth_spans = dict()
    for gt_label in article.labels:
        # A single span in our benchmark could have several true labels
        if gt_label.span not in ground_truth_spans:
            ground_truth_spans[gt_label.span] = []
        ground_truth_spans[gt_label.span].append(gt_label.id)

    cases = []

    label_dict = dict()
    for gt_label in article.labels:
        label_dict[gt_label.id] = gt_label

    # ground truth cases:
    for gt_label in sorted(article.labels):
        span = gt_label.span
        text = article.text[span[0]:span[1]]
        detected = span in predictions
        predicted_mention = None
        if detected:
            predicted_mention = predictions[span]
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
                # If parent span = child span, parent factor is only 0 if child entity id matches predicted entity id
                if child.span in predictions and (gt_label.span != child.span or
                                                  (predicted_entity and child.entity_id == predicted_entity.entity_id)):
                    factor = 0
                    break
        elif gt_label.parent:
            # If gt_label is child of a parent label that was detected, or if none of the parents children were detected
            # don't count child label -> factor = 0
            parent = label_dict[gt_label.parent]
            if parent.span in predictions and gt_label.span != parent.span or\
                    (predicted_entity and gt_label.entity_id != predicted_entity.entity_id):
                factor = 0
            else:
                sibling_detected = False
                for sibling_id in parent.children:
                    sibling = label_dict[sibling_id]
                    if sibling.span in predictions:
                        sibling_detected = True
                        if predictions[sibling.span].entity_id != sibling.entity_id:
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
        predicted_mention = predictions[span]

        candidates = set()
        for cand_id in predicted_mention.candidates:
            if entity_db.contains_entity(cand_id):
                candidates.add(WikidataEntity(entity_db.get_entity(cand_id).name, 0, cand_id, []))

        predicted_entity_id = predicted_mention.entity_id
        predicted_entity_name = entity_db.get_entity(predicted_entity_id).name \
            if entity_db.contains_entity(predicted_entity_id) else "Unknown"
        predicted_entity = WikidataEntity(predicted_entity_name, 0, predicted_mention.entity_id, [])

        if span not in ground_truth_spans and predicted_entity_id is not None and span[0] >= evaluation_span[0] \
                and span[1] <= evaluation_span[1]:
            text = article.text[span[0]:span[1]]
            predicted_by = predicted_mention.linked_by
            contained = predicted_mention.contained
            case = Case(span, text, None, True, predicted_entity, contained=contained, candidates=candidates,
                        predicted_by=predicted_by, referenced_span=predicted_mention.referenced_span, factor=1)
            cases.append(case)

    return sorted(cases)
