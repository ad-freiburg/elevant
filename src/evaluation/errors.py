from typing import List, Set, Tuple, Optional

from itertools import chain

from src.evaluation.case import Case, ErrorLabel
from src.evaluation.groundtruth_label import GroundtruthLabel
from src.evaluation.mention_type import MentionType, is_named_entity
from src.models.entity_database import EntityDatabase
from src.models.wikidata_entity import WikidataEntity
from src.models.article import Article


def label_errors(article: Article,
                 cases: List[Case],
                 entity_db: EntityDatabase,
                 contains_unknowns: bool):
    text = article.text
    unknown_ground_truth_spans = {case.span for case in cases if case.has_ground_truth()
                                  and not case.is_known_entity()}
    cases = [case for case in cases if (case.is_false_positive() or case.is_known_entity())]
    label_undetected_errors(cases)
    label_correct(cases, entity_db)
    label_disambiguation_errors(cases, entity_db)
    label_false_detections(cases, unknown_ground_truth_spans, contains_unknowns)
    label_nonentity_coreference_errors(text, cases)
    label_candidate_errors(cases)
    label_multi_candidates(cases)
    label_hyperlink_errors(article, cases)
    label_span_errors(cases)
    label_coreference_errors(cases)


def is_subspan(span: Tuple[int, int], subspan: Tuple[int, int]) -> bool:
    """
    Check if subspan is contained in span.
    """
    if span[0] == subspan[0] and span[1] == subspan[1]:
        return False
    return span[0] <= subspan[0] and span[1] >= subspan[1]


def is_specificity_error(case: Case, false_positive_spans: List[Tuple[int, int]]) -> bool:
    """
    A false positive span is subspan of the ground truth span.
    """
    for fp_span in false_positive_spans:
        if is_subspan(case.span, fp_span):
            return True
    return False


def label_undetected_errors(cases: List[Case]):
    """
    Label undetected mentions as undetected and one of:
    - undetected lowercase
    - specificity
    - undetected overlap
    - undetected other
    """
    false_positive_spans = [case.span for case in cases if case.is_false_positive()]
    for case in cases:
        if case.is_not_coreference() and case.is_false_negative() and case.predicted_entity is None:
            case.add_error_label(ErrorLabel.UNDETECTED)
            if not is_named_entity(case.text):
                case.add_error_label(ErrorLabel.UNDETECTED_LOWERCASE)
            elif is_specificity_error(case, false_positive_spans):
                case.add_error_label(ErrorLabel.UNDETECTED_PARTIALLY_INCLUDED)
            elif overlaps_any(case.span, false_positive_spans):
                case.add_error_label(ErrorLabel.UNDETECTED_PARTIAL_OVERLAP)
            else:
                case.add_error_label(ErrorLabel.UNDETECTED_OTHER)


DEMONYM_TYPES = {"Q27096213", "Q41710", "Q17376908"}


def is_demonym(case: Case, entity_db: EntityDatabase) -> bool:
    """
    Mention is contained in the list of demonyms and ground truth type is location, ethnicity or languoid.
    """
    if not entity_db.is_demonym(case.text):
        return False
    types = set(case.true_entity.type.split("|"))
    return bool(types.intersection(DEMONYM_TYPES))


def is_partial_name(case: Case) -> bool:
    """
    The ground truth entity name is a multi word, and the mention is contained in it.
    """
    name = case.true_entity.name
    return " " in name and len(case.text) < len(name) and case.text in name


def is_rare_case(case: Case, entity_db: EntityDatabase) -> bool:
    """
    The most popular candidate is not the ground truth entity.
    """
    most_popular_candidate = get_most_popular_candidate(entity_db, case.text)
    return most_popular_candidate and case.true_entity.entity_id != most_popular_candidate


def label_correct(cases: List[Case], entity_db: EntityDatabase):
    """
    Label correct predictions with one of (or no label):
    - demonym correct
    - metonymy correct
    - partial name correct
    - rare correct
    """
    for case in cases:
        if case.is_not_coreference() and case.is_correct():
            if is_demonym(case, entity_db):
                case.add_error_label(ErrorLabel.DISAMBIGUATION_DEMONYM_CORRECT)
            elif is_metonymy(case, entity_db):
                case.add_error_label(ErrorLabel.DISAMBIGUATION_METONYMY_CORRECT)
            elif is_partial_name(case):
                case.add_error_label(ErrorLabel.DISAMBIGUATION_PARTIAL_NAME_CORRECT)
            elif is_rare_case(case, entity_db):
                case.add_error_label(ErrorLabel.DISAMBIGUATION_RARE_CORRECT)


LOCATION_TYPE_ID = "Q27096213"
PERSON_TYPE_QID = "Q18336849"
ETHNICITY_TYPE_ID = "Q41710"


def get_most_popular_candidate(entity_db: EntityDatabase, alias: str) -> Optional[str]:
    """
    Returns the entity ID of the most popular candidate for the given alias, or None if no candidate exists.
    """
    candidates = entity_db.get_candidates(alias)
    if len(candidates) == 0:
        return None
    _, most_popular_candidate = max((entity_db.get_sitelink_count(c), c) for c in candidates)
    return most_popular_candidate


def is_location_alias(text: str, entity_db: EntityDatabase) -> bool:
    """
    The most popular candidate is a location.
    """
    most_popular_candidate = get_most_popular_candidate(entity_db, text)
    if not most_popular_candidate:
        return False
    most_popular_entity = entity_db.get_entity(most_popular_candidate)
    types = most_popular_entity.type.split("|")
    return LOCATION_TYPE_ID in types


def is_metonymy(case: Case, entity_db: EntityDatabase) -> bool:
    """
    The most popular candidate is a location, and the ground truth is neither a location, person nor ethnicity.
    """
    true_types = case.true_entity.type.split("|")
    if LOCATION_TYPE_ID in true_types or PERSON_TYPE_QID in true_types or ETHNICITY_TYPE_ID in true_types:
        return False
    most_popular_candidate = get_most_popular_candidate(entity_db, case.text)
    if not most_popular_candidate:
        return False
    most_popular_entity = entity_db.get_entity(most_popular_candidate)
    most_popular_types = most_popular_entity.type.split("|")
    return LOCATION_TYPE_ID in most_popular_types


def is_metonymy_error(case: Case, entity_db: EntityDatabase) -> bool:
    """
    Same as is_metonymy(), and the predicted entity is a location.
    """
    if not is_metonymy(case, entity_db):
        return False
    predicted_types = case.predicted_entity.type.split("|")
    return LOCATION_TYPE_ID in predicted_types


def label_disambiguation_errors(cases: List[Case],
                                entity_db: EntityDatabase):
    """
    Mention was detected, but linked to the wrong entity.
    Cases get labeled with disambiguation errors, and one of the following:
    - demonym wrong
    - metonymy wrong
    - partial name wrong
    - rare wrong
    - disambiguation other
    """
    for case in cases:
        if case.is_not_coreference() and case.is_false_negative() and case.is_false_positive():
            case.add_error_label(ErrorLabel.DISAMBIGUATION_WRONG)
            if is_demonym(case, entity_db):
                case.add_error_label(ErrorLabel.DISAMBIGUATION_DEMONYM_WRONG)
            elif is_metonymy_error(case, entity_db):
                case.add_error_label(ErrorLabel.DISAMBIGUATION_METONYMY_WRONG)
            elif is_partial_name(case):
                case.add_error_label(ErrorLabel.DISAMBIGUATION_PARTIAL_NAME_WRONG)
            elif is_rare_case(case, entity_db) and \
                    case.predicted_entity.entity_id == get_most_popular_candidate(entity_db, case.text):
                case.add_error_label(ErrorLabel.DISAMBIGUATION_RARE_WRONG)
            else:
                case.add_error_label(ErrorLabel.DISAMBIGUATION_WRONG_OTHER)


NONENTITY_PRONOUNS = {"it", "this", "that", "its"}


def label_nonentity_coreference_errors(text: str, cases: List[Case]):
    for case in cases:
        if case.is_optional():
            continue
        if not case.has_ground_truth():
            snippet = text[case.span[0]:case.span[1]]
            if len(snippet) > 1 and snippet[0].lower() + snippet[1:] in NONENTITY_PRONOUNS:
                case.add_error_label(ErrorLabel.COREFERENCE_FALSE_DETECTION)


def label_candidate_errors(cases: List[Case]):
    for case in cases:
        if case.is_false_negative() and not case.is_coreference() and case.is_false_positive() and \
                not case.true_entity_is_candidate():
            case.add_error_label(ErrorLabel.DISAMBIGUATION_WRONG_CANDIDATES)


def label_multi_candidates(cases: List[Case]):
    for case in cases:
        if case.has_ground_truth() and len(case.candidates) > 1 and case.true_entity_is_candidate():
            if case.is_correct():
                case.add_error_label(ErrorLabel.DISAMBIGUATION_MULTI_CANDIDATES_CORRECT)
            elif not case.is_optional() or case.is_false_positive():
                # If the case is optional and not correct, but a "FN", don't add error label, just ignore it
                case.add_error_label(ErrorLabel.DISAMBIGUATION_MULTI_CANDIDATES_WRONG)


def overlaps(span1: Tuple[int, int], span2: Tuple[int, int]) -> bool:
    return not (span1[0] >= span2[1] or span2[0] >= span1[1])


def overlaps_any(span: Tuple[int, int], spans: List[Tuple[int, int]]) -> bool:
    """
    Span overlaps with any of the spans.
    """
    for other in spans:
        if overlaps(span, other):
            return True
    return False


def contains_uppercase_word(text: str) -> bool:
    for word in text.split():
        if len(word) > 0 and word[0].isupper():
            return True
    return False


def label_false_detections(cases: List[Case],
                           unknown_ground_truth_spans: Set[Tuple[int, int]],
                           contains_unknowns: bool):
    """
    Labels false positives with false positive and one of the following:
    - abstraction
    - unknown named entity
    - false positive other

    If contains_unknowns is true, unknown named entity is labeled when the ground truth is 'Unknown'.
    Otherwise, it is also labeled when the mention does not overlap with any ground truth (because unknown labels can
    be missing, e.g. in the MSNBC and ACE benchmarks).
    """
    ground_truth_spans = [case.span for case in cases if case.has_ground_truth()]
    for case in cases:
        if case.is_not_coreference() and case.is_false_positive() and not case.is_known_entity():
            case.add_error_label(ErrorLabel.FALSE_DETECTION)
            overlap = False
            for gt_span in chain(ground_truth_spans, unknown_ground_truth_spans):
                if overlaps(case.span, gt_span):
                    overlap = True
                    break
            contains_upper = contains_uppercase_word(case.text)
            if not overlap and not contains_upper:
                case.add_error_label(ErrorLabel.FALSE_DETECTION_ABSTRACT_ENTITY)
            elif contains_upper and \
                    ((not overlap and not contains_unknowns) or case.span in unknown_ground_truth_spans):
                case.add_error_label(ErrorLabel.FALSE_DETECTION_UNKNOWN_ENTITY)
            else:
                case.add_error_label(ErrorLabel.FALSE_DETECTION_OTHER)


def label_hyperlink_errors(article: Article, cases: List[Case]):
    hyperlink_spans = set(span for span, target in article.hyperlinks)
    for case in cases:
        if case.span in hyperlink_spans and case.has_ground_truth() and case.is_known_entity():
            if case.is_correct() or case.is_true_quantity_or_datetime():
                case.add_error_label(ErrorLabel.HYPERLINK_CORRECT)
            elif (not case.is_optional() and not case.is_nil_entity()) or case.is_false_positive():
                # If the case is optional and not correct, but a "FN", don't add error label, just ignore it
                case.add_error_label(ErrorLabel.HYPERLINK_WRONG)


def label_coreference_errors(cases: List[Case]):
    for i, case in enumerate(cases):
        if case.is_coreference() and case.is_false_negative():
            if not case.has_predicted_entity():
                # Coreference FN
                case.add_error_label(ErrorLabel.COREFERENCE_UNDETECTED)
            else:
                # Coreference FN + FP = disambiguation error
                true_reference = None
                for j in range(i - 1, -1, -1):
                    if cases[j].mention_type == MentionType.ENTITY_NAMED and cases[j].has_ground_truth() and \
                            cases[j].true_entity.entity_id == case.true_entity.entity_id:
                        true_reference = cases[j]
                        break
                if true_reference is not None:
                    if true_reference.has_predicted_entity() and \
                            true_reference.predicted_entity.entity_id == case.predicted_entity.entity_id:
                        case.add_error_label(ErrorLabel.COREFERENCE_REFERENCE_WRONGLY_DISAMBIGUATED)
                    else:
                        case.add_error_label(ErrorLabel.COREFERENCE_WRONG_MENTION_REFERENCED)


def label_span_errors(cases: List[Case]):
    """
    False positives, that overlap with a ground truth mention with the same entity id.
    """
    ground_truth = {case.span: case.true_entity for case in cases if case.has_ground_truth()}
    for case in cases:
        if case.is_false_positive():
            for gt_span in ground_truth:
                gt_label = ground_truth[gt_span]
                if gt_span == case.span:
                    # Span is correct -> no need to consider it
                    continue
                if overlaps(case.span, gt_span) and (case.predicted_entity.entity_id == gt_label.entity_id or
                                                     is_true_quantity_or_datetime(case.predicted_entity, gt_label)):
                    # Span is wrong and entity id is correct or it's a true quantity or datetime.
                    case.add_error_label(ErrorLabel.FALSE_DETECTION_WRONG_SPAN)
                    break


def is_true_quantity_or_datetime(predicted_entity: WikidataEntity, gt_label: GroundtruthLabel) -> bool:
    return gt_label.type == predicted_entity.type and (gt_label.is_datetime() or gt_label.is_quantity())
