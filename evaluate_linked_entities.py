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

from src.evaluation.benchmark import Benchmark
from src.evaluation.case import case_from_dict
from src.evaluation.examples_generator import get_example_generator
from src.models.wikipedia_article import article_from_json
from src.evaluation.evaluator import Evaluator
from src import settings


def main(args):
    input_file = open(args.input_file, 'r', encoding='utf8')
    idx = args.input_file.rfind('.')

    output_file = None
    case_file = None
    output_filename = None

    # Get a dictionary with whitelist types for all predicted entities (ground truth labels already have a type)
    print("Get whitelist-types for all predicted entities...")
    predicted_entity_ids = set()
    for line in input_file:
        article = article_from_json(line)
        predicted_entity_ids.update([em.entity_id for em in article.entity_mentions.values()])
    # Go through the entity to type mapping
    id_to_type = dict()
    with open(settings.WHITELIST_TYPE_MAPPING, "r", encoding="utf8") as file:
        for line in file:
            lst = line.strip().split("\t")
            entity_id = lst[0][:-1].split("/")[-1]
            # name = lst[1][1:-3]
            whitelist_type = lst[2][:-1].split("/")[-1]
            if entity_id in predicted_entity_ids:
                if entity_id not in id_to_type:  # An entity can have multiple types from the whitelist
                    id_to_type[entity_id] = []
                id_to_type[entity_id].append(whitelist_type)

    if args.input_case_file:
        case_file = open(args.input_case_file, 'r', encoding='utf8')
        evaluator = Evaluator(id_to_type, load_data=False, coreference=not args.no_coreference)
    else:
        output_filename = args.output_file if args.output_file else args.input_file[:idx] + ".cases"
        output_file = open(output_filename, 'w', encoding='utf8')
        print("load evaluation entities...")
        evaluator = Evaluator(id_to_type, load_data=True)
    results_file = (args.output_file[:-6] if args.output_file else args.input_file[:idx]) + ".results"

    example_iterator = None
    if args.benchmark:
        # If a benchmark is given, labels are retrieved from the benchmark
        # and not from the given jsonl file. The user has to make sure the files match.
        example_iterator = get_example_generator(args.benchmark).iterate()

    input_file.seek(0)
    for line in input_file:
        article = article_from_json(line)
        if example_iterator:
            benchmark_article = next(example_iterator)
            article.labels = benchmark_article.labels

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
    parser.add_argument("-b", "--benchmark", choices=[b.value for b in Benchmark], default=None,
                        help="Benchmark over which to evaluate the linked entities. If none is given, labels are"
                             "retrieved from the given jsonl file")

    main(parser.parse_args())
