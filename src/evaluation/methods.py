from src.evaluation.case import Case
from src.linkers.abstract_coref_linker import AbstractCorefLinker
from src.models.wikidata_entity import WikidataEntity
from src.models.wikipedia_article import WikipediaArticle


def get_evaluation_cases(article: WikipediaArticle,
                         ground_truth,
                         coref_ground_truth,
                         entity_db):
    predictions = article.entity_mentions
    evaluation_span = article.evaluation_span

    ground_truth_spans = set(span for span, _ in ground_truth)

    cases = []

    # ground truth cases:
    for span, true_entity_id in sorted(ground_truth):
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

        case = Case(span, text, true_entity, detected, predicted_entity, candidates, predicted_by,
                    contained=contained,
                    is_true_coref=is_true_coref,
                    correct_span_referenced=correct_span_referenced,
                    referenced_span=referenced_span)
        cases.append(case)

    # predicted cases (potential false detections):
    for span in predictions:
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
                        predicted_by=predicted_by, referenced_span=predicted_mention.referenced_span)
            cases.append(case)

    return sorted(cases)
