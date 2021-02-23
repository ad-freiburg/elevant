import json
from typing import Tuple, Dict, List, Optional

from termcolor import colored
from src.evaluation.case import CASE_COLORS, CaseType, ErrorLabel, Case
from src.linkers.abstract_coref_linker import AbstractCorefLinker


def percentage(nominator: int, denominator: int) -> Tuple[float, int, int]:
    if denominator == 0:
        percent = 0
    else:
        percent = nominator / denominator * 100
    return percent, nominator, denominator


def create_f1_dict(tp, fp, fn):
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


def print_colored_text(cases, text):
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


def print_article_nerd_evaluation(cases, text):
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


def print_article_coref_evaluation(cases, text):
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


def print_evaluation_summary(evaluator):
    all_cases = evaluator.all_cases
    counts = evaluator.counts
    n_total = n_correct = n_known = n_detected = n_contained = n_is_candidate = n_true_in_multiple_candidates = \
        n_correct_multiple_candidates = n_false_positives = n_false_negatives = n_ground_truth = n_false_detection = \
        n_coref_total = n_coref_tp = n_coref_fp = 0
    for case in all_cases:
        n_total += 1

        if case.is_coreference():
            if case.is_true_coreference():
                n_coref_total += 1
                if case.is_correct():
                    n_coref_tp += 1
                else:
                    n_coref_fp += 1
            if not case.is_true_coreference():
                n_coref_fp += 1
        else:
            if case.has_ground_truth():
                n_ground_truth += 1
                if case.is_known_entity():
                    n_known += 1
                    if case.contained:
                        n_contained += 1
                    if case.is_detected():
                        n_detected += 1
                        if case.true_entity_is_candidate():
                            n_is_candidate += 1
                            if len(case.candidates) > 1:
                                n_true_in_multiple_candidates += 1
                                if case.is_correct():
                                    n_correct_multiple_candidates += 1

        if case.is_correct():
            n_correct += 1
        elif case.is_known_entity():
            n_false_negatives += 1
        if case.is_false_positive():
            n_false_positives += 1
        if case.eval_type == CaseType.FALSE_DETECTION:
            n_false_detection += 1

    n_unknown = n_ground_truth - n_known
    n_undetected = n_known - n_detected

    print("\n== EVALUATION ==")
    print("%i ground truth entity mentions evaluated" % n_ground_truth)
    print("\t%.2f%% correct (%i/%i)" % percentage(n_correct, n_ground_truth))
    print("\t%.2f%% not a known entity (%i/%i)" % percentage(n_unknown, n_ground_truth))
    print("\t%.2f%% known entities (%i/%i)" % percentage(n_known, n_ground_truth))
    print("\t\t%.2f%% correct (%i/%i)" % percentage(n_correct, n_known))
    print("\t\t%.2f%% contained (%i/%i)" % percentage(n_contained, n_known))
    print("\t\t%.2f%% not detected (%i/%i)" % percentage(n_undetected, n_known))
    print("\t\t%.2f%% detected (%i/%i)" % percentage(n_detected, n_known))
    print("\t\t\t%.2f%% correct (%i/%i)" % percentage(n_correct, n_detected))
    # TODO: Link-linker and coreference-linker do not yield candidate information
    print("\t\t\t%.2f%% true entity in candidates (%i/%i)" % percentage(n_is_candidate, n_detected))
    print("\t\t\t\t%.2f%% correct (%i/%i)" % percentage(n_correct, n_is_candidate))
    print("\t\t\t\t%.2f%% multiple candidates (%i/%i)" % percentage(n_true_in_multiple_candidates, n_is_candidate))
    print("\t\t\t\t\t%.2f%% correct (%i/%i)" % percentage(n_correct_multiple_candidates,
                                                          n_true_in_multiple_candidates))

    print()
    print("Coreference evaluation:")
    print("\tprecision = %.2f%% (%i/%i)" % percentage(n_coref_tp, n_coref_tp + n_coref_fp))
    print("\trecall =    %.2f%% (%i/%i)" % percentage(n_coref_tp, n_coref_total))
    coref_precision = n_coref_tp / (n_coref_tp + n_coref_fp)
    coref_recall = n_coref_tp / n_coref_total
    coref_f1 = 2 * coref_precision * coref_recall / (coref_precision + coref_recall)\
        if (coref_precision + coref_recall) > 0 else 0
    print("\tf1 =        %.2f%%" % (coref_f1*100))

    print("\nNER:")
    ner_precision, ner_prec_nominator, ner_prec_denominator = percentage(counts["NER"]["tp"],
                                                                         counts["NER"]["tp"] + counts["NER"]["fp"])
    print("precision = %.2f%% (%i/%i)" % (ner_precision, ner_prec_nominator, ner_prec_denominator))
    ner_recall, ner_rec_nominator, ner_rec_denominator = percentage(counts["NER"]["tp"],
                                                                    counts["NER"]["tp"] + counts["NER"]["fn"])
    print("recall =    %.2f%% (%i/%i)" % (ner_recall, ner_rec_nominator, ner_rec_denominator))
    ner_precision = ner_precision / 100
    ner_recall = ner_recall / 100
    ner_f1 = 2 * ner_precision * ner_recall / (ner_precision + ner_recall) if (ner_precision + ner_recall) > 0 else 0
    print("f1 =        %.2f%%" % (ner_f1 * 100))

    print("\nNERD:")
    print("tp = %i, fp = %i (false detections = %i), fn = %i" %
          (n_correct, n_false_positives, n_false_detection, n_false_negatives))
    precision, prec_nominator, prec_denominator = percentage(n_correct, n_correct + n_false_positives)
    print("precision = %.2f%% (%i/%i)" % (precision, prec_nominator, prec_denominator))
    recall, rec_nominator, rec_denominator = percentage(n_correct, n_correct + n_false_negatives)
    print("recall =    %.2f%% (%i/%i)" % (recall, rec_nominator, rec_denominator))
    precision = precision / 100
    recall = recall / 100
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    print("f1 =        %.2f%%" % (f1 * 100))
