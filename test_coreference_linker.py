import argparse

from termcolor import colored

from src.abstract_coref_linker import AbstractCorefLinker
from src.entity_coref_linker import EntityCorefLinker
from src.entity_database import EntityDatabase
from src.neuralcoref_coref_linker import NeuralcorefCorefLinker
from src.coreference_groundtruth_generator import CoreferenceGroundtruthGenerator
from src.evaluation_examples_generator import OwnBenchmarkExampleReader
from src.stanford_corenlp_coref_linker import StanfordCoreNLPCorefLinker
from src.xrenner_coref_linker import XrennerCorefLinker
from test_entity_linker import CaseType, CASE_COLORS, Case, percentage
from src.wikipedia_article import article_from_json


def print_help():
    print("Usage:\n"
          "    python3 <n_articles>\n"
          "\n"
          "Arguments:\n"
          "    <linker>: type of coreference linker. Choose one of {neuralcoref, entity}"
          "    <n_articles>: Number of articles to evaluate on.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-n", "--n_articles", type=int, default=-1,
                        help="Number of articles to evaluate on.")

    parser.add_argument("linker_type", choices=['neuralcoref', 'entity', 'stanford', 'xrenner'],
                        help="Type of coreference linker.")

    parser.add_argument("--linked_file", type=str, default=None,
                        help="Read existing linked entities from file.")

    args = parser.parse_args()

    if args.linker_type == "neuralcoref":
        coreference_linker = NeuralcorefCorefLinker()
    elif args.linker_type == "stanford":
        coreference_linker = StanfordCoreNLPCorefLinker()
    elif args.linker_type == "xrenner":
        coreference_linker = XrennerCorefLinker()
    else:
        entity_db = EntityDatabase()
        print("load gender information...")
        entity_db.load_gender()
        coreference_linker = EntityCorefLinker(entity_db)

    coref_groundtruth_generator = CoreferenceGroundtruthGenerator()

    example_generator = OwnBenchmarkExampleReader()

    linked_file = None
    if args.linked_file:
        linked_file = open(args.linked_file, "r")

    all_cases = []
    for article, ground_truth, evaluation_span in example_generator.iterate(args.n_articles):
        text = article.text
        coref_groundtruth = coref_groundtruth_generator.get_groundtruth(article)

        if linked_file:
            json_line = linked_file.readline()
            article = article_from_json(json_line)

        predictions = coreference_linker.predict(article, only_pronouns=True, evaluation_span=evaluation_span)
        ground_truth_spans = set(span for span, _ in ground_truth)
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

        cases = sorted(cases)

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

        all_cases.extend(cases)

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
