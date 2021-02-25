from typing import List

from src.evaluation.case import Case, ErrorLabel
from src.evaluation.mention_type import MentionType
from src.models.entity_database import EntityDatabase


def label_errors(text: str, cases: List[Case], entity_db: EntityDatabase):
    cases = [case for case in cases if case.is_false_positive() or case.is_known_entity()]  # do not label unknowns
    label_specificity_errors(cases)
    label_demonym_errors(text, cases, entity_db)
    label_rare_entity_errors(text, cases, entity_db)
    label_partial_name_errors(text, cases, entity_db)
    label_nonentity_coreference_errors(text, cases)
    label_detection_errors(cases)
    label_candidate_errors(cases)
    label_multi_candidates(cases)
    label_abstraction_errors(cases)


def is_subspan(span, subspan):
    if span[0] == subspan[0] and span[1] == subspan[1]:
        return False
    return span[0] <= subspan[0] and span[1] >= subspan[1]


def label_specificity_errors(cases: List[Case]):
    false_negatives = [case for case in cases if case.has_predicted_entity() and not case.is_true_coreference()]
    false_positives = [case for case in cases if case.is_false_positive()]
    for case in false_negatives:
        for fp in false_positives:
            if is_subspan(case.span, fp.span):
                case.add_error_label(ErrorLabel.SPECIFICITY)
                break


def label_demonym_errors(text: str, cases: List[Case], entity_db: EntityDatabase):
    for case in cases:
        if not case.is_correct() and case.true_entity is not None:
            mention = text[case.span[0]:case.span[1]]
            if entity_db.is_demonym(mention):
                case.add_error_label(ErrorLabel.DEMONYM)


def label_rare_entity_errors(text: str, cases: List[Case], entity_db: EntityDatabase):
    for case in cases:
        if not case.is_correct() and case.true_entity is not None and case.predicted_entity is not None\
                and not case.is_true_coreference():
            mention = text[case.span[0]:case.span[1]]
            if not entity_db.is_demonym(mention):
                if entity_db.get_sitelink_count(case.true_entity.entity_id) \
                        < entity_db.get_sitelink_count(case.predicted_entity.entity_id):
                    case.add_error_label(ErrorLabel.RARE)


def label_partial_name_errors(text: str, cases: List[Case], entity_db: EntityDatabase):
    for case in cases:
        if not case.is_correct() and case.true_entity is not None and not case.is_true_coreference():
            mention = text[case.span[0]:case.span[1]]
            if not entity_db.is_demonym(mention):
                name = case.true_entity.name
                if len(mention) < len(name) and mention in name.split():
                    case.add_error_label(ErrorLabel.PARTIAL_NAME)


NONENTITY_PRONOUNS = {"it", "this", "that", "its"}


def label_nonentity_coreference_errors(text: str, cases: List[Case]):
    for case in cases:
        if not case.has_ground_truth():
            snippet = text[case.span[0]:case.span[1]]
            if snippet[0].lower() + snippet[1:] in NONENTITY_PRONOUNS:
                case.add_error_label(ErrorLabel.NON_ENTITY_COREFERENCE)


def label_detection_errors(cases: List[Case]):
    for case in cases:
        if not case.is_coreference() and not case.has_predicted_entity():
            case.add_error_label(ErrorLabel.UNDETECTED)
            if case.text.islower():
                case.add_error_label(ErrorLabel.UNDETECTED_LOWERCASE)


def label_candidate_errors(cases: List[Case]):
    for case in cases:
        if case.is_false_negative() and not case.is_coreference() and case.is_detected() and \
                not case.true_entity_is_candidate():
            case.add_error_label(ErrorLabel.WRONG_CANDIDATES)


def label_multi_candidates(cases: List[Case]):
    for case in cases:
        if case.has_ground_truth() and len(case.candidates) > 1 and case.true_entity_is_candidate():
            if case.is_correct():
                case.add_error_label(ErrorLabel.MULTI_CANDIDATES_CORRECT)
            else:
                case.add_error_label(ErrorLabel.MULTI_CANDIDATES_WRONG)


def overlaps(span1, span2):
    return not (span1[0] >= span2[1] or span2[0] >= span1[1])


def label_abstraction_errors(cases: List[Case]):
    ground_truth_spans = [case.span for case in cases if case.has_ground_truth()]
    for case in cases:
        if case.is_false_positive() and case.mention_type == MentionType.NAMED:
            overlap = False
            for gt_span in ground_truth_spans:
                if overlaps(case.span, gt_span):
                    overlap = True
                    break
            if not overlap:
                case.add_error_label(ErrorLabel.ABSTRACTION)
