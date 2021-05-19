from src.evaluation.case import Case, JOKER_LABELS
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

    joker_spans = []
    for gt_label in article.labels:
        if gt_label.entity_id in JOKER_LABELS:
            joker_spans.append(gt_label.span)
    joker_spans.sort()

    cases = []

    label_dict = dict()
    for gt_label in article.labels:
        label_dict[gt_label.id] = gt_label

    # ground truth cases:
    for gt_label in sorted(article.labels):
        span, true_entity_id = gt_label.span, gt_label.entity_id
        text = article.text[span[0]:span[1]]
        true_entity_name = entity_db.get_entity(true_entity_id).name \
            if entity_db.contains_entity(true_entity_id) else "Unknown"
        true_entity = WikidataEntity(true_entity_name, 0, true_entity_id, [])
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
            predicted_entity = WikidataEntity(predicted_entity_name, 0, predicted_mention.entity_id, [])
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
        if gt_label.children:
            for child_id in gt_label.children:
                child = label_dict[child_id]
                if child.span in predictions:
                    factor = 0
                    break
        elif gt_label.parent:
            # If gt_label is child of a parent label that was detected, or if none of the parents children were detected
            # don't count child label -> factor = 0
            parent = label_dict[gt_label.parent]
            if parent.span in predictions:
                factor = 0
            else:
                sibling_detected = False
                for sibling_id in parent.children:
                    sibling = label_dict[sibling_id]
                    if sibling.span in predictions:
                        sibling_detected = True
                        break
                if not sibling_detected:
                    factor = 0

        case = Case(span, text, true_entity, detected, predicted_entity, candidates, predicted_by,
                    contained=contained,
                    is_true_coref=is_true_coref,
                    correct_span_referenced=correct_span_referenced,
                    referenced_span=referenced_span,
                    factor=factor)
        cases.append(case)

    # predicted cases (potential false detections):
    curr_joker_span_idx = 0
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

        # For datetimes or quantities we also want to consider predicted mentions as joker, if the span is not
        # identical to the joker groundtruth span, but is included in it. Other overlaps are errors for now.
        is_joker = False
        while curr_joker_span_idx < len(joker_spans):
            joker_span = joker_spans[curr_joker_span_idx]
            if span[0] >= joker_span[0] and span[1] <= joker_span[1]:
                is_joker = True
                break
            if span[1] <= joker_span[1]:
                break
            curr_joker_span_idx += 1

        if span not in ground_truth_spans and predicted_entity_id is not None and span[0] >= evaluation_span[0] \
                and span[1] <= evaluation_span[1]:
            text = article.text[span[0]:span[1]]
            predicted_by = predicted_mention.linked_by
            contained = predicted_mention.contained
            case = Case(span, text, None, True, predicted_entity, contained=contained, candidates=candidates,
                        predicted_by=predicted_by, referenced_span=predicted_mention.referenced_span, factor=1,
                        part_of_joker=is_joker)
            cases.append(case)

    return sorted(cases)
