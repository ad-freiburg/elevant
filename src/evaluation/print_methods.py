from typing import Tuple, Dict, List

from termcolor import colored
from src.evaluation.case import CASE_COLORS, CaseType, Case
from src.linkers.abstract_coref_linker import AbstractCorefLinker


def percentage(nominator: int, denominator: int) -> Tuple[float, int, int]:
    if denominator == 0:
        percent = 0
    else:
        percent = nominator / denominator * 100
    return percent, nominator, denominator


def create_f1_dict(tp: int, fp: int, fn: int) -> Dict:
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    ground_truth = tp + fn
    recall = tp / ground_truth if ground_truth > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "ground_truth": ground_truth,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }


def create_f1_dict_from_counts(counts: Dict):
    return create_f1_dict(counts["tp"], counts["fp"], counts["fn"])


def print_colored_text(cases: List[Case], text: str):
    colored_spans = [(case.span, CASE_COLORS[case.eval_type]) for case in cases
                     if case.eval_type != CaseType.UNKNOWN_ENTITY]
    i = 0
    while i + 1 < len(colored_spans):
        span, color = colored_spans[i]
        next_span, next_color = colored_spans[i + 1]
        if span[1] > next_span[0]:
            left_span = (span[0], next_span[0]), color
            mid_span = (next_span[0], span[1]), CASE_COLORS["mixed"]
            right_span = (span[1], next_span[1]), next_color
            colored_spans = colored_spans[:i] + [left_span, mid_span, right_span] + colored_spans[(i + 2):]
        i += 1

    print_str = ""
    position = 0
    for span, color in colored_spans:
        begin, end = span
        print_str += text[position:begin]
        print_str += colored(text[begin:end], color=color)
        position = end
    print_str += text[position:]
    print(print_str)


def print_article_nerd_evaluation(cases: List[Case], text: str):
    for case in cases:
        true_str = "(%s %s)" % (case.true_entity.entity_id, case.true_entity.name) \
            if case.true_entity is not None else "None"
        referenced_span = " -> %s" % (str(case.referenced_span)) \
            if case.predicted_by == AbstractCorefLinker.IDENTIFIER else ""
        predicted_str = "(%s %s [%s]%s)" % (case.predicted_entity.entity_id, case.predicted_entity.name
                                            if case.predicted_entity else "Unknown",
                                            case.predicted_by, referenced_span) \
            if case.predicted_entity is not None else "None"
        error_labels = ",".join(label.value for label in case.error_labels)
        print(colored("  %s %s %s %s %i %s %s" % (str(case.span),
                                                  text[case.span[0]:case.span[1]],
                                                  true_str,
                                                  predicted_str,
                                                  case.n_candidates(),
                                                  case.eval_type.name,
                                                  error_labels),
                      color=CASE_COLORS[case.eval_type]))


def print_article_coref_evaluation(cases: List[Case], text: str):
    coref_cases = [c for c in cases
                   if c.is_true_coreference() or c.predicted_by == AbstractCorefLinker.IDENTIFIER]
    print("Coreference Cases:")
    for case in coref_cases:
        true_str = "(%s %s)" % (case.true_entity.entity_id, case.true_entity.name) \
            if case.true_entity is not None else "None"
        referenced_span = " -> %s %s" % (str(case.referenced_span), text[case.referenced_span[0]:
                                                                         case.referenced_span[1]])\
            if case.predicted_by == AbstractCorefLinker.IDENTIFIER else ""
        predicted_str = "(%s %s %s)" % (case.predicted_entity.entity_id,
                                        case.predicted_entity.name,
                                        referenced_span) \
            if case.predicted_entity is not None else "None"
        print(colored("  %s %s %s %s %i %s" % (str(case.span),
                                               text[case.span[0]:case.span[1]],
                                               true_str,
                                               predicted_str,
                                               case.n_candidates(),
                                               case.coref_type.name),
                      color=CASE_COLORS[case.coref_type]))


def print_evaluation_summary(counts: Dict):
    print("== EVALUATION ==")
    for category in counts:
        print()
        print("= %s =" % category)
        f1_dict = create_f1_dict(counts[category]["tp"], counts[category]["fp"], counts[category]["fn"])
        print("precision:\t%.2f%%" % (f1_dict["precision"] * 100))
        print("recall:\t\t%.2f%%" % (f1_dict["recall"] * 100))
        print("f1:\t\t%.2f%%" % (f1_dict["f1"] * 100))
