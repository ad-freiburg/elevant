"""
Evaluates entity linking.
This takes a jsonl file produced by link_benchmark_entities.py with one linked
article and its ground truth labels per line.
The resulting evaluation cases are written to an output file in jsonl format
with one case per line.
The evaluation results are printed.
"""

import argparse
import json

from src.evaluation.case import case_from_dict
from src.models.wikipedia_article import article_from_json
from src.evaluation.evaluator import Evaluator


def main(args):
    input_file = open(args.input_file, 'r', encoding='utf8')
    idx = args.input_file.rfind('.')

    output_file = None
    case_file = None
    output_filename = None
    if args.input_case_file:
        case_file = open(args.input_case_file, 'r', encoding='utf8')
        evaluator = Evaluator(load_data=False,
                              coreference=not args.no_coreference)
    else:
        output_filename = args.output_file if args.output_file else args.input_file[:idx] + ".cases"
        output_file = open(output_filename, 'w', encoding='utf8')
        print("load evaluation entities...")
        evaluator = Evaluator(load_data=True)
    results_file = (args.output_file[:-6] if args.output_file else args.input_file[:idx]) + ".results"

    for line in input_file:
        article = article_from_json(line)

        if args.input_case_file:
            dump = json.loads(case_file.readline())
            cases = [case_from_dict(case_dict) for case_dict in dump]
        else:
            cases = evaluator.get_cases(article)
        evaluator.add_cases(cases)
        evaluator.print_article_evaluation(article, cases)

        if not args.input_case_file:
            case_list = [case.to_dict() for case in cases]
            output_file.write(json.dumps(case_list) + "\n")

    evaluator.print_results()

    with open(results_file, "w") as f:
        f.write(json.dumps(evaluator.get_results_dict()))
    print("\nWrote results to %s" % results_file)

    input_file.close()
    if args.input_case_file:
        case_file.close()
    else:
        output_file.close()
        print("\nWrote evaluation cases to %s" % output_filename)


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
                        help="Exclude coreference cases from the evaluation.")

    main(parser.parse_args())
