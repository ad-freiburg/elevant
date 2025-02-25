from typing import List, Tuple, Set

from elevant import settings
from elevant.evaluation.case import Case, ErrorLabel, EvaluationMode
from elevant.evaluation.groundtruth_label import GroundtruthLabel
from elevant.evaluation.mention_type import MentionType, is_non_named_entity
from elevant.models.entity_database import EntityDatabase
from elevant.models.wikidata_entity import WikidataEntity
from elevant.models.article import Article

from elevant.evaluation.benchmark_case import BenchmarkCaseLabel


def label_errors(article: Article,
                 cases: List[Case],
                 entity_db: EntityDatabase,
                 eval_mode: EvaluationMode,
                 contains_unknowns: bool):
    cases = [case for case in cases if case.true_entity is None or case.true_entity.parent is None]
    label_undetected_errors(cases, eval_mode)
    label_disambiguation_errors(cases, entity_db, eval_mode)
    label_false_detections(cases, contains_unknowns, eval_mode)
    label_candidate_errors(cases, eval_mode)
    label_multi_candidates(cases, eval_mode)
    label_hyperlink_errors(article, cases, eval_mode)
    label_span_errors(cases, eval_mode)
    label_coreference_errors(cases, eval_mode)
    label_correct(cases, entity_db, eval_mode)


def is_subspan(span: Tuple[int, int], subspan: Tuple[int, int]) -> bool:
    """
    Check if subspan is contained in span.
    """
    if span[0] == subspan[0] and span[1] == subspan[1]:
        return False
    return span[0] <= subspan[0] and span[1] >= subspan[1]


def is_partially_included_error(case: Case, false_positive_spans: List[Tuple[int, int]]) -> bool:
    """
    A false positive span is subspan of the ground truth span.
    """
    for fp_span in false_positive_spans:
        if is_subspan(case.span, fp_span):
            return True
    return False


def label_undetected_errors(cases: List[Case], eval_mode: EvaluationMode):
    """
    Label undetected mentions as undetected and one of:
    - undetected lowercase
    - specificity
    - undetected overlap
    - undetected other
    """
    false_positive_spans = [case.span for case in cases if case.is_ner_fp(eval_mode)]
    for case in cases:
        if not case.is_coreference() and case.is_ner_fn(eval_mode):
            case.add_error_label(ErrorLabel.NER_FN, eval_mode)
            if is_non_named_entity(case.text):
                case.add_error_label(ErrorLabel.NER_FN_LOWERCASED, eval_mode)
            elif is_partially_included_error(case, false_positive_spans):
                case.add_error_label(ErrorLabel.NER_FN_PARTIALLY_INCLUDED, eval_mode)
            elif overlaps_any(case.span, false_positive_spans):
                case.add_error_label(ErrorLabel.NER_FN_PARTIAL_OVERLAP, eval_mode)
            else:
                case.add_error_label(ErrorLabel.NER_FN_OTHER, eval_mode)


DEMONYM_TYPES = {settings.TYPE_LOCATION_QID, settings.TYPE_ETHNICITY_QID, settings.TYPE_LANGUOID_QID}


def is_demonym(case: Case, entity_db: EntityDatabase) -> bool:
    """
    Mention is contained in the list of demonyms and ground truth type is location, ethnicity or languoid.
    """
    if not entity_db.is_demonym(case.text):
        return False
    types = set(entity_db.get_entity_types(case.true_entity.entity_id))
    return bool(types.intersection(DEMONYM_TYPES))


def is_partial_name(case: Case) -> bool:
    """
    The ground truth entity name is a multi word, and the mention is contained in it.
    """
    if not case.ground_truth_has_known_entity_id():
        # Cases with unknown groundtruth are not considered as partial name errors
        return False
    name = case.true_entity.name
    return " " in name and len(case.text) < len(name) and case.text in name


def is_rare_case(case: Case, entity_db: EntityDatabase) -> bool:
    """
    The most popular candidate is not the ground truth entity.
    """
    most_popular_candidates = get_most_popular_candidate(entity_db, case.text)
    # Right now, this is always true when the entity is Unknown and there exists at least one candidate.
    # So many evaluated cases with unknown GT are automatically rare errors.
    return most_popular_candidates and case.true_entity.entity_id not in most_popular_candidates


def label_correct(cases: List[Case], entity_db: EntityDatabase, eval_mode: EvaluationMode):
    """
    Label correct predictions with one of (or no label):
    - demonym correct
    - metonymy correct
    - partial name correct
    - rare correct
    """
    for case in cases:
        if not case.is_coreference():
            if case.is_linking_tp(eval_mode):
                # Label correct disambiguation cases
                case.add_error_label(ErrorLabel.DISAMBIGUATION_CORRECT, eval_mode)
                if is_demonym(case, entity_db):
                    case.add_error_label(ErrorLabel.DISAMBIGUATION_DEMONYM_CORRECT, eval_mode)
                elif is_metonymy(case, entity_db):
                    case.add_error_label(ErrorLabel.DISAMBIGUATION_METONYMY_CORRECT, eval_mode)
                elif is_partial_name(case):
                    case.add_error_label(ErrorLabel.DISAMBIGUATION_PARTIAL_NAME_CORRECT, eval_mode)
                elif is_rare_case(case, entity_db):
                    case.add_error_label(ErrorLabel.DISAMBIGUATION_RARE_CORRECT, eval_mode)
                else:
                    case.add_error_label(ErrorLabel.DISAMBIGUATION_OTHER_CORRECT, eval_mode)
            # Label potential NER FN error cases
            if case.is_ner_tp(eval_mode):
                case.add_error_label(ErrorLabel.AVOIDED_NER_FN, eval_mode)
            if (case.is_ner_tp(eval_mode) or case.is_ner_fp(eval_mode)) and \
                    ErrorLabel.NER_FP_WRONG_SPAN not in case.error_labels[eval_mode]:
                case.add_error_label(ErrorLabel.AVOIDED_NER_FP_WRONG_SPAN, eval_mode)
            if is_non_named_entity(case.text):
                # Label NER TP lowercased cases
                if case.is_ner_tp(eval_mode):
                    case.add_error_label(ErrorLabel.AVOIDED_NER_FN_LOWERCASED, eval_mode)
            elif ' ' in case.text:
                # Note: Checking for mentions that contain a whitespace is only an approximation for where partially
                # included errors can be made. Some linkers e.g. would link only "U.S." in "U.S.-based" or
                # "Ala" in "Ala." or "US" in "US$". This results in different denominators for different linkers
                # (since such a linker would get +1 error there).
                # This is very rare though. E.g. TagMe's denominator on AIDA-CoNLL is 6 greater than ReFinED's.
                if (case.is_ner_tp(eval_mode) or case.is_ner_fn(eval_mode)) \
                        and ErrorLabel.NER_FN_PARTIALLY_INCLUDED not in case.error_labels[eval_mode]:
                    # Label cases where a partially included error could potentially have happened but did not
                    case.add_error_label(ErrorLabel.AVOIDED_NER_FN_PARTIALLY_INCLUDED, eval_mode)
            if not is_non_named_entity(case.text) and (case.is_ner_tp(eval_mode) or case.is_ner_fn(eval_mode)):
                if ErrorLabel.NER_FN_PARTIAL_OVERLAP not in case.error_labels[eval_mode]:
                    case.add_error_label(ErrorLabel.AVOIDED_NER_FN_PARTIAL_OVERLAP, eval_mode)
                if ErrorLabel.NER_FN_OTHER not in case.error_labels[eval_mode]:
                    case.add_error_label(ErrorLabel.AVOIDED_NER_FN_OTHER, eval_mode)
            # Label avoided GT unknown cases
            if (not is_non_named_entity(case.text) and case.has_ground_truth() and case.ground_truth_is_unknown_entity()
                    and not case.is_ner_fp(eval_mode)):
                case.add_error_label(ErrorLabel.AVOIDED_NER_FP_GROUNDTRUTH_UNKNOWN, eval_mode)


def get_benchmark_case_labels(case: Case, entity_db: EntityDatabase):
    if not case.ground_truth_has_known_entity_id():
        # Unknown ground truth cases should not be considered rare errors.
        # Demonym is the only acceptable error label for unknown ground truth cases, but even that is
        # weird since the problem is that something was linked and not that language/ethnicity/country got mixed up.
        return
    if case.is_coreference():
        # Coreference cases are not considered for the categorization into disambiguation errors, and are instead
        # categorized into fine-grained coreference error categories.
        # None of our disambiguation error categories make sense for coreferences
        return
    if is_demonym(case, entity_db):
        return BenchmarkCaseLabel.DEMONYM
    elif is_metonymy(case, entity_db):
        return BenchmarkCaseLabel.METONYM
    elif is_partial_name(case):
        return BenchmarkCaseLabel.PARTIAL_NAME
    elif is_rare_case(case, entity_db):
        return BenchmarkCaseLabel.RARE


def get_most_popular_candidate(entity_db: EntityDatabase, alias: str) -> Set[str]:
    """
    Returns the entity ID of the most popular candidate for the given alias, or None if no candidate exists
    or all link frequencies are 0.
    """
    # Use the link frequency and not the sitelink count to get the most popular candidate. Otherwise, since we're
    # including link aliases, it would be enough if a more popular entity was linked once with the alias in Wikipedia,
    # e.g. France would be a rare error, because it was at least once falsly linked to Turkey in Wikipedia.
    most_popular_candidates = entity_db.get_most_popular_candidate_for_hyperlink(alias)
    return most_popular_candidates


def is_metonymy(case: Case, entity_db: EntityDatabase) -> bool:
    """
    The most popular candidate is a location, and the ground truth is neither a location, person nor ethnicity.
    """
    if not case.ground_truth_has_known_entity_id():
        # Cases with unknown groundtruth are not considered as metonymy errors
        return False
    true_types = entity_db.get_entity_types(case.true_entity.entity_id)
    if settings.TYPE_LOCATION_QID in true_types or settings.TYPE_PERSON_QID in true_types or settings.TYPE_ETHNICITY_QID in true_types or \
            settings.TYPE_FICTIONAL_CHARACTER_QID in true_types:
        return False
    most_popular_candidates = get_most_popular_candidate(entity_db, case.text)
    if not most_popular_candidates:
        return False
    # It counts as metonymy if any one of the most popular candidates (often there'll be only one) is a location
    most_popular_entity_types = set()
    for candidate in most_popular_candidates:
        most_popular_entity_types |= set(entity_db.get_entity_types(candidate))
    return settings.TYPE_LOCATION_QID in most_popular_entity_types


def is_metonymy_error(case: Case, entity_db: EntityDatabase) -> bool:
    """
    Same as is_metonymy(), and the predicted entity is a location.
    """
    if not is_metonymy(case, entity_db):
        return False
    predicted_types = entity_db.get_entity_types(case.predicted_entity.entity_id)
    return settings.TYPE_LOCATION_QID in predicted_types


def label_disambiguation_errors(cases: List[Case], entity_db: EntityDatabase, eval_mode: EvaluationMode):
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
        if not case.is_coreference() and case.is_linking_fn(eval_mode) and case.is_linking_fp(eval_mode):
            case.add_error_label(ErrorLabel.DISAMBIGUATION_WRONG, eval_mode)
            if is_demonym(case, entity_db):
                case.add_error_label(ErrorLabel.DISAMBIGUATION_DEMONYM_WRONG, eval_mode)
            elif is_metonymy_error(case, entity_db):
                case.add_error_label(ErrorLabel.DISAMBIGUATION_METONYMY_WRONG, eval_mode)
            elif is_partial_name(case):
                case.add_error_label(ErrorLabel.DISAMBIGUATION_PARTIAL_NAME_WRONG, eval_mode)
            elif is_rare_case(case, entity_db) and \
                    case.predicted_entity.entity_id in get_most_popular_candidate(entity_db, case.text):
                case.add_error_label(ErrorLabel.DISAMBIGUATION_RARE_WRONG, eval_mode)
            else:
                case.add_error_label(ErrorLabel.DISAMBIGUATION_OTHER_WRONG, eval_mode)


def label_candidate_errors(cases: List[Case], eval_mode: EvaluationMode):
    for case in cases:
        if not case.is_coreference() and case.is_ner_tp(eval_mode):
            if case.is_linking_tp(eval_mode) or case.true_entity_is_candidate():
                case.add_error_label(ErrorLabel.DISAMBIGUATION_CANDIDATES_CORRECT, eval_mode)
            elif case.is_linking_fn(eval_mode) and case.is_linking_fp(eval_mode) and not case.true_entity_is_candidate():
                case.add_error_label(ErrorLabel.DISAMBIGUATION_CANDIDATES_WRONG, eval_mode)


def label_multi_candidates(cases: List[Case], eval_mode: EvaluationMode):
    for case in cases:
        if not case.is_coreference() and case.has_ground_truth() and len(case.candidates) > 1 and \
                case.true_entity_is_candidate():
            if case.is_linking_tp(eval_mode):
                case.add_error_label(ErrorLabel.DISAMBIGUATION_MULTI_CANDIDATES_CORRECT, eval_mode)
            elif case.is_linking_fn(eval_mode) and case.is_linking_fp(eval_mode):
                case.add_error_label(ErrorLabel.DISAMBIGUATION_MULTI_CANDIDATES_WRONG, eval_mode)


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
                           contains_unknowns: bool,
                           eval_mode: EvaluationMode):
    """
    Labels false positives with false positive and one of the following:
    - abstraction
    - unknown named entity
    - false positive other

    If contains_unknowns is true, unknown named entity is labeled when the ground truth is 'Unknown'.
    Otherwise, it is also labeled when the mention does not overlap with any ground truth (because unknown labels can
    be missing, e.g. in the MSNBC and ACE benchmarks).
    """
    ground_truth_spans = [case.span for case in cases if case.has_relevant_ground_truth(eval_mode)]

    for case in cases:
        if not case.is_coreference() and case.is_ner_fp(eval_mode):
            case.add_error_label(ErrorLabel.NER_FP, eval_mode)
            overlap = False
            for gt_span in ground_truth_spans:
                if overlaps(case.span, gt_span):
                    overlap = True
                    break
            # contains_upper = contains_uppercase_word(case.text)
            if not overlap and is_non_named_entity(case.text):
                case.add_error_label(ErrorLabel.NER_FP_LOWERCASED, eval_mode)
            elif not is_non_named_entity(case.text) and \
                    ((not overlap and not contains_unknowns) or (case.has_ground_truth() and
                                                                 case.ground_truth_is_unknown_entity())):
                case.add_error_label(ErrorLabel.NER_FP_GROUNDTRUTH_UNKNOWN, eval_mode)
            else:
                case.add_error_label(ErrorLabel.NER_FP_OTHER, eval_mode)


def label_hyperlink_errors(article: Article, cases: List[Case], eval_mode: EvaluationMode):
    hyperlink_spans = set(span for span, target in article.hyperlinks)
    for case in cases:
        if case.span in hyperlink_spans:
            if case.is_linking_tp(eval_mode):
                case.add_error_label(ErrorLabel.HYPERLINK_CORRECT, eval_mode)
            elif case.is_linking_fn(eval_mode) or case.is_linking_fp(eval_mode):
                case.add_error_label(ErrorLabel.HYPERLINK_WRONG, eval_mode)


def label_coreference_errors(cases: List[Case], eval_mode):
    for i, case in enumerate(cases):
        if case.is_coreference():
            if case.is_ner_fp(eval_mode):
                # Coreference NER FP
                case.add_error_label(ErrorLabel.COREFERENCE_FALSE_DETECTION, eval_mode)
            elif case.is_ner_fn(eval_mode):
                # Coreference NER FN
                case.add_error_label(ErrorLabel.COREFERENCE_UNDETECTED, eval_mode)
            elif case.is_linking_fn(eval_mode) and case.is_linking_fp(eval_mode):
                # Coreference FN + FP = disambiguation error
                true_reference = None
                for j in range(i - 1, -1, -1):
                    if cases[j].mention_type == MentionType.ENTITY_NAMED and cases[j].has_ground_truth() and \
                            cases[j].true_entity.entity_id == case.true_entity.entity_id:
                        true_reference = cases[j]
                        break
                if true_reference is not None:
                    if true_reference.prediction_is_known() and \
                            true_reference.predicted_entity.entity_id == case.predicted_entity.entity_id:
                        case.add_error_label(ErrorLabel.COREFERENCE_REFERENCE_WRONGLY_DISAMBIGUATED, eval_mode)
                    else:
                        case.add_error_label(ErrorLabel.COREFERENCE_WRONG_MENTION_REFERENCED, eval_mode)


def label_span_errors(cases: List[Case], eval_mode: EvaluationMode):
    """
    False positives, that overlap with a ground truth mention with the same entity id.
    """
    ground_truth_spans = {case.span: case.true_entity for case in cases if case.has_relevant_ground_truth(eval_mode)}
    for case in cases:
        if case.is_ner_fp(eval_mode):
            for gt_span in ground_truth_spans:
                gt_label = ground_truth_spans[gt_span]
                if gt_span == case.span:
                    # Span is correct -> no need to consider it
                    continue
                if overlaps(case.span, gt_span) and (case.predicted_entity.entity_id == gt_label.entity_id or
                                                     is_true_quantity_or_datetime(case.predicted_entity, gt_label)):
                    # Span is wrong and entity id is correct or it's a true quantity or datetime.
                    case.add_error_label(ErrorLabel.NER_FP_WRONG_SPAN, eval_mode)
                    break


def is_true_quantity_or_datetime(predicted_entity: WikidataEntity, gt_label: GroundtruthLabel) -> bool:
    return gt_label.type == predicted_entity.type and (gt_label.is_datetime() or gt_label.is_quantity())
