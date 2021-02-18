"""
Evaluates entity linking.
This takes a jsonl file produced by link_benchmark_entities.py with one linked
article and its ground truth labels per line.
The resulting evaluation cases are written to an output file in jsonl format
with one case per line.
The evaluation results are printed.
"""

from typing import Tuple
import argparse
import json

from termcolor import colored

from src.linkers.abstract_coref_linker import AbstractCorefLinker
from src.models.case import Case, CASE_COLORS, CaseType, case_from_dict
from src.helpers.coreference_groundtruth_generator import is_coreference, CoreferenceGroundtruthGenerator
from src.models.entity_database import EntityDatabase
from src.helpers.evaluation_examples_generator import get_ground_truth_from_labels
from src.models.wikidata_entity import WikidataEntity
from src.models.wikipedia_article import article_from_json


def percentage(nominator: int, denominator: int) -> Tuple[float, int, int]:
    if denominator == 0:
        percent = 0
    else:
        percent = nominator / denominator * 100
    return percent, nominator, denominator


def load_evaluation_entities():
    entity_db = EntityDatabase()
    entity_db.load_entities_big()
    entity_db.load_mapping()
    entity_db.load_redirects()
    return entity_db


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


def get_evaluation_cases(predictions, ground_truth, coref_ground_truth, evaluation_span, entity_db):
    ground_truth_spans = set(span for span, _ in ground_truth)

    cases = []

    # ground truth cases:
    for span, true_entity_id in sorted(ground_truth):
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

        case = Case(span, true_entity, detected, predicted_entity, candidates, predicted_by, contained=contained,
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
            predicted_by = predicted_mention.linked_by
            contained = predicted_mention.contained
            case = Case(span, None, True, predicted_entity, contained=contained, candidates=candidates,
                        predicted_by=predicted_by, referenced_span=predicted_mention.referenced_span)
            cases.append(case)

    return sorted(cases)


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


def evaluate_ner(predictions, ground_truth, evaluation_span):
    ground_truth_spans = set(span for span, _ in ground_truth)

    # NER evaluation:
    predicted_spans = set(predictions)
    eval_begin, eval_end = evaluation_span
    predicted_spans = {(begin, end) for begin, end in predicted_spans
                       if begin >= eval_begin and end <= eval_end}
    ner_tp = ground_truth_spans.intersection(predicted_spans)
    ner_fp = predicted_spans.difference(ground_truth_spans)
    ner_fn = ground_truth_spans.difference(predicted_spans)
    return ner_tp, ner_fp, ner_fn


"""
def print_article_ner_evaluation(ner_tp, ner_fp, ner_fn, text, linker, max_match_ner):
    print("NER TP:", sorted([(span, text[span[0]:span[1]],
                              linker.get_alias_frequency(text[span[0]:span[1]])
                              if max_match_ner else 0)
                             for span in ner_tp]))
    print("NER FP:", sorted([(span, text[span[0]:span[1]],
                              linker.get_alias_frequency(text[span[0]:span[1]])
                              if max_match_ner else 0)
                             for span in ner_fp]))
    print("NER FN:", sorted([(span, text[span[0]:span[1]],
                              linker.get_alias_frequency(text[span[0]:span[1]])
                              if max_match_ner else 0)
                             for span in ner_fn]))
"""


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
        print(colored("  %s %s %s %s %i %s" % (str(case.span),
                                               text[case.span[0]:case.span[1]],
                                               true_str,
                                               predicted_str,
                                               case.n_candidates(),
                                               case.eval_type.name),
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


def print_evaluation_summary(all_cases, n_ner_tp, n_ner_fp, n_ner_fn,
                             output_file=None):
    n_total = n_correct = n_known = n_detected = n_contained = n_is_candidate = n_true_in_multiple_candidates = \
        n_correct_multiple_candidates = n_false_positives = n_false_negatives = n_ground_truth = n_false_detection = \
        n_coref_total = n_coref_tp = n_coref_fp = 0
    for case in all_cases:
        n_total += 1

        if case.is_true_coreference():
            n_coref_total += 1
            if case.correct_span_referenced:
                n_coref_tp += 1
            else:
                n_coref_fp += 1
        if case.predicted_by == AbstractCorefLinker.IDENTIFIER:
            if not case.is_true_coreference():
                n_coref_fp += 1

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
    ner_precision, ner_prec_nominator, ner_prec_denominator = percentage(n_ner_tp, n_ner_tp + n_ner_fp)
    print("precision = %.2f%% (%i/%i)" % (ner_precision, ner_prec_nominator, ner_prec_denominator))
    ner_recall, ner_rec_nominator, ner_rec_denominator = percentage(n_ner_tp, n_ner_tp + n_ner_fn)
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

    if output_file is not None:
        results_dict = {
            "all": create_f1_dict(n_correct, n_false_positives, n_false_negatives),
            "NER": create_f1_dict(n_ner_tp, n_ner_fp, n_ner_fn),
            "coreference": create_f1_dict(n_coref_tp, n_coref_fp, n_coref_total - n_coref_tp),
            "named": create_f1_dict(0, 0, 0),
            "nominal": create_f1_dict(0, 0, 0),
            "pronominal": create_f1_dict(0, 0, 0),
            "cases": {
                "correct": n_correct,
                "known": n_contained,
                "detected": n_detected,
                "correct_candidate": n_is_candidate,
                "multi_candidate": {
                    "correct": n_correct_multiple_candidates,
                    "wrong": n_true_in_multiple_candidates - n_correct_multiple_candidates
                }
            },
            "errors": {
                "non_entity_coreference": 0,
                "rare": 0,
                "specificity": 0,
                "demonym": 0,
                "partial_name": 0,
                "abstraction": 0
            }
        }
        results_json = json.dumps(results_dict)
        with open(output_file, "w") as f:
            f.write(results_json)


def main(args):
    input_file = open(args.input_file, 'r', encoding='utf8')
    idx = args.input_file.rfind('.')

    output_file = None
    case_file = None
    entity_db = None
    output_filename = None
    if args.input_case_file:
        case_file = open(args.input_case_file, 'r', encoding='utf8')
    else:
        output_filename = args.output_file if args.output_file else args.input_file[:idx] + ".cases"
        output_file = open(output_filename, 'w', encoding='utf8')
        print("load evaluation entities...")
        entity_db = load_evaluation_entities()
    results_file = (args.output_file[:-6] if args.output_file else args.input_file[:idx]) + ".results"

    all_cases = []
    n_ner_tp = n_ner_fp = n_ner_fn = 0
    for line in input_file:
        article = article_from_json(line)
        ground_truth = get_ground_truth_from_labels(article.labels)
        if args.no_coreference:
            ground_truth = [(span, entity_id) for span, entity_id in ground_truth
                            if not is_coreference(article.text[span[0]:span[1]])]

        if args.input_case_file:
            dump = json.loads(case_file.readline())
            cases = [case_from_dict(case_dict) for case_dict in dump]
        else:
            coref_ground_truth = CoreferenceGroundtruthGenerator.get_groundtruth(article)

            cases = get_evaluation_cases(article.entity_mentions, ground_truth, coref_ground_truth,
                                         article.evaluation_span, entity_db)

        print_colored_text(cases, article.text)

        ner_tp, ner_fp, ner_fn = evaluate_ner(article.entity_mentions, ground_truth, article.evaluation_span)
        n_ner_tp += len(ner_tp)
        n_ner_fp += len(ner_fp)
        n_ner_fn += len(ner_fn)

        print_article_nerd_evaluation(cases, article.text)
        print_article_coref_evaluation(cases, article.text)

        if not args.input_case_file:
            case_list = [case.to_dict() for case in cases]
            output_file.write(json.dumps(case_list) + "\n")

        all_cases.extend(cases)

    print_evaluation_summary(all_cases, n_ner_tp, n_ner_fp, n_ner_fn, output_file=results_file)
    print("Wrote results to %s" % results_file)

    input_file.close()
    if args.input_case_file:
        case_file.close()
    else:
        output_file.close()
        print()
        print("Wrote evaluation cases to %s" % output_filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("input_file", type=str,
                        help="Input file. Linked articles with ground truth labels.")
    parser.add_argument("-out", "--output_file", type=str, default=None,
                        help="Output file for the evaluation results."
                             " The input file with .cases extension if none is specified.")
    parser.add_argument("-in", "--input_case_file", type=str, default=None,
                        help="Input file that contains the evaluation cases. Cases are not written to file.")
    parser.add_argument("--no_coreference", action="store_true",
                        help="Exclude coreference cases from the evalutation.")

    main(parser.parse_args())
