import argparse
import json

from termcolor import colored

from evaluate_linked_entities import percentage
from link_benchmark_entities import initialize_example_generator
from src.linkers.abstract_coref_linker import AbstractCorefLinker
from src.evaluation.case import Case, CASE_COLORS, CaseType, case_from_dict
from src.evaluation.coreference_groundtruth_generator import CoreferenceGroundtruthGenerator
from src.linkers.entity_coref_linker import EntityCorefLinker
from src.models.entity_database import EntityDatabase
from src.linkers.hobbs_coref_linker import HobbsCorefLinker
from src.linkers.neuralcoref_coref_linker import NeuralcorefCorefLinker
from src.linkers.stanford_corenlp_coref_linker import StanfordCoreNLPCorefLinker
from src.models.wikipedia_article import article_from_json
from src.linkers.xrenner_coref_linker import XrennerCorefLinker


def initialize_coref_linker(linker_type):
    if linker_type == "neuralcoref":
        coreference_linker = NeuralcorefCorefLinker()
    elif linker_type == "stanford":
        coreference_linker = StanfordCoreNLPCorefLinker()
    elif linker_type == "xrenner":
        coreference_linker = XrennerCorefLinker()
    elif linker_type == "hobbs":
        entity_db = EntityDatabase()
        coreference_linker = HobbsCorefLinker(entity_db)
    else:
        entity_db = EntityDatabase()
        coreference_linker = EntityCorefLinker(entity_db)
    return coreference_linker


def get_coref_evaluation_cases(predictions, coref_groundtruth, evaluation_span):
    cases = []

    # ground truth cases:
    for span, poss_ref_spans in sorted(coref_groundtruth.items()):
        detected = span in predictions
        correct_span_referenced = False
        referenced_span = None
        if detected:
            referenced_span = predictions[span]
            for poss_ref_span in poss_ref_spans:
                # Do not require a perfect match of the spans but look for overlaps
                if poss_ref_span[0] <= referenced_span[1] <= poss_ref_span[1] or \
                        poss_ref_span[0] <= referenced_span[0] <= poss_ref_span[1] or \
                        (poss_ref_span[0] > referenced_span[0] and poss_ref_span[1] < referenced_span[1]):
                    correct_span_referenced = True
                    break

        case = Case(span, None, detected, None, candidates=set(), predicted_by=AbstractCorefLinker.IDENTIFIER,
                    is_true_coref=True, correct_span_referenced=correct_span_referenced,
                    referenced_span=referenced_span)
        cases.append(case)

    # predicted cases (potential false detections):
    for span in predictions:
        referenced_span = predictions[span]
        if span not in coref_groundtruth and span[0] >= evaluation_span[0] and span[1] <= evaluation_span[1]:
            case = Case(span, None, True, None, candidates=set(), is_true_coref=False,
                        predicted_by=AbstractCorefLinker.IDENTIFIER, referenced_span=referenced_span)
            cases.append(case)

    return sorted(cases)


def print_colored_text(cases, text):
    colored_spans = [(case.span, CASE_COLORS[case.coref_type]) for case in cases
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


def print_article_coref_cases(cases, text):
    print("Coreference Cases:")
    coref_cases = [c for c in cases
                   if c.is_true_coreference() or c.predicted_by == AbstractCorefLinker.IDENTIFIER]
    for case in coref_cases:
        referenced_span = " -> %s %s" % (str(case.referenced_span), text[case.referenced_span[0]:
                                                                         case.referenced_span[1]]) \
            if case.referenced_span else ""
        print(colored("  %s %s %s %s" % (str(case.span),
                                         text[case.span[0]:case.span[1]],
                                         referenced_span,
                                         case.coref_type.name),
                      color=CASE_COLORS[case.coref_type]))


def print_evaluation_summary(all_cases):
    n_total = n_coref_total = n_coref_tp = n_coref_fp = 0
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

    print("\n== EVALUATION ==")
    print("Coreference evaluation:")
    print("\tprecision = %.2f%% (%i/%i)" % percentage(n_coref_tp, n_coref_tp + n_coref_fp))
    print("\trecall =    %.2f%% (%i/%i)" % percentage(n_coref_tp, n_coref_total))
    precision = n_coref_tp / (n_coref_tp + n_coref_fp)
    recall = n_coref_tp / n_coref_total
    f1 = 2 * precision * recall / (precision + recall)
    print("\tf1 =        %.2f%%" % (f1*100))


def main(args):
    coreference_linker = None
    if not args.input_case_file:
        coreference_linker = initialize_coref_linker(args.linker_type)

    example_generator = initialize_example_generator(args.benchmark)

    linked_file = None
    if args.linked_file:
        linked_file = open(args.linked_file, "r")

    output_file = None
    case_file = None
    if args.input_case_file:
        case_file = open(args.input_case_file, 'r', encoding='utf8')
    elif args.output_file:
        output_file = open(args.output_file, 'w', encoding='utf8')

    all_cases = []
    for i, article in enumerate(example_generator.iterate(args.n_articles)):
        coref_ground_truth = CoreferenceGroundtruthGenerator.get_groundtruth(article)

        if args.input_case_file:
            dump = json.loads(case_file.readline())
            cases = [case_from_dict(case_dict) for case_dict in dump]
        else:
            if linked_file:
                json_line = linked_file.readline()
                linked_article = article_from_json(json_line)
                predictions = coreference_linker.predict(linked_article, only_pronouns=args.only_pronouns,
                                                         evaluation_span=article.evaluation_span)
            else:
                predictions = coreference_linker.predict(article, only_pronouns=args.only_pronouns,
                                                         evaluation_span=article.evaluation_span)
            cases = get_coref_evaluation_cases(predictions, coref_ground_truth, article.evaluation_span)

        print_colored_text(cases, article.text)
        print_article_coref_cases(cases, article.text)

        if args.output_file:
            case_list = [case.to_dict() for case in cases]
            output_file.write(json.dumps(case_list) + "\n")

        all_cases.extend(cases)

    print_evaluation_summary(all_cases)

    if args.input_case_file:
        case_file.close()
    elif args.output_file:
        output_file.close()
        print()
        print("Wrote evaluation cases to %s" % args.output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("linker_type", choices=['neuralcoref', 'entity', 'stanford', 'xrenner', 'hobbs'],
                        help="Type of coreference linker.")

    parser.add_argument("-out", "--output_file", type=str,
                        help="Output file for the evaluation results.")

    parser.add_argument("-in", "--input_case_file", type=str, default=None,
                        help="Input file that contains the evaluation cases. Cases are then not written to outputfile.")

    parser.add_argument("-n", "--n_articles", type=int, default=-1,
                        help="Number of articles to evaluate on.")

    parser.add_argument("-lf", "--linked_file", type=str, default=None,
                        help="Read existing linked entities from file. Needed for entity and hobbs linker.")

    parser.add_argument("--only_pronouns", action="store_true",
                        help="Only link coreferences that are pronouns.")

    parser.add_argument("-b", "--benchmark", choices=["own", "wikipedia", "conll"], default="own",
                        help="Benchmark over which to evaluate the linker.")

    main(parser.parse_args())
