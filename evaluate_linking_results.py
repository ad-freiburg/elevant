"""
Evaluates entity linking.
This takes a jsonl file produced by link_benchmark_entities.py with one linked
article and its ground truth labels per line.
The resulting evaluation cases are written to an output file in jsonl format
with one case per line.
The evaluation results are printed.
"""

import argparse
import log
import sys
import json
import re

from src import settings
from src.evaluation.benchmark import get_available_benchmarks
from src.evaluation.benchmark_iterator import get_benchmark_iterator
from src.models.article import article_from_json
from src.evaluation.evaluator import Evaluator


def main(args):
    logger.info("Evaluating linking results from %s ..." % args.input_files)

    # Read whitelist types
    whitelist_types = set()
    if args.type_whitelist:
        with open(args.type_whitelist, 'r', encoding='utf8') as file:
            for line in file:
                type_match = re.search(r"Q[0-9]+", line)
                if type_match:
                    typ = type_match.group(0)
                    whitelist_types.add(typ)

    whitelist_file = settings.WHITELIST_FILE
    if args.type_whitelist:
        whitelist_file = args.type_whitelist
    elif args.custom_mappings:
        whitelist_file = settings.CUSTOM_WHITELIST_TYPES_FILE

    type_mapping_file = args.type_mapping if args.type_mapping else settings.QID_TO_WHITELIST_TYPES_DB
    evaluator = Evaluator(type_mapping_file, whitelist_file=whitelist_file, contains_unknowns=not args.no_unknowns,
                          custom_mappings=args.custom_mappings)

    for input_file_name in args.input_files:
        idx = input_file_name.rfind('.linked_articles.jsonl')
        output_filename = args.output_file if args.output_file else input_file_name[:idx] + ".eval_cases.jsonl"
        output_file = open(output_filename, 'w', encoding='utf8')
        results_file = (args.output_file[:-len(".eval_cases.jsonl")] if args.output_file else input_file_name[:idx]) \
            + ".eval_results.json"

        benchmark_iterator = None
        if args.benchmark:
            # If a benchmark is given, labels and article texts are retrieved from the benchmark
            # and not from the given jsonl file. The user has to make sure the files match.
            logger.info("Retrieving labels from %s benchmark file instead of %s" % (args.benchmark, input_file_name))
            benchmark_iterator = get_benchmark_iterator(args.benchmark).iterate()

        logger.info("Evaluating linking results ...")
        input_file = open(input_file_name, 'r', encoding='utf8')
        for line in input_file:
            article = article_from_json(line)
            if benchmark_iterator:
                benchmark_article = next(benchmark_iterator)
                article.labels = benchmark_article.labels
                article.text = benchmark_article.text

            if args.type_mapping:
                # Map benchmark label entities to types in the mapping
                for gt_label in article.labels:
                    types = evaluator.entity_db.get_entity_types(gt_label.entity_id)
                    gt_label.type = types.join("|")

            if whitelist_types:
                # Ignore groundtruth labels that do not have a type that is included in the whitelist
                filtered_labels = []
                added_label_ids = set()
                for gt_label in article.labels:
                    # Only consider parent labels. Child types can not be counted, since otherwise we
                    # would end up with fractional TP/FN
                    # Add all children of a parent as well. This works because article.labels are sorted -
                    # parents always come before children
                    if gt_label.parent is None or gt_label.parent in added_label_ids:
                        types = gt_label.get_types()
                        for typ in types:
                            if typ in whitelist_types or gt_label.parent is not None \
                                    or gt_label.entity_id.startswith("Unknown"):
                                filtered_labels.append(gt_label)
                                added_label_ids.add(gt_label.id)
                                break
                article.labels = filtered_labels

                # If the type_filter_predictions argument is set, ignore predictions that do
                # not have a type that is included in the whitelist
                filtered_entity_mentions = {}
                if args.type_filter_predictions:
                    for span, em in article.entity_mentions.items():
                        types = evaluator.entity_db.get_entity_types(em.entity_id)
                        for typ in types:
                            if typ in whitelist_types:
                                filtered_entity_mentions[span] = em
                                break
                    article.entity_mentions = filtered_entity_mentions

            cases = evaluator.evaluate_article(article)

            case_list = [case.to_dict() for case in cases]
            output_file.write(json.dumps(case_list) + "\n")

        results_dict = evaluator.get_results_dict()
        evaluator.print_results()
        evaluator.reset_variables()

        with open(results_file, "w") as f:
            f.write(json.dumps(results_dict))
        logger.info("Wrote results to %s" % results_file)

        if args.benchmark and args.write_labels:
            input_file.seek(0)
            input_file_lines = input_file.readlines()
            input_file.close()
            with open(input_file_name, 'w', encoding='utf8') as file:
                benchmark_iterator = get_benchmark_iterator(args.benchmark).iterate()
                for line in input_file_lines:
                    article = article_from_json(line)
                    benchmark_article = next(benchmark_iterator)
                    article.labels = benchmark_article.labels
                    file.write(article.to_json() + "\n")
        else:
            input_file.close()

        output_file.close()
        logger.info("Wrote evaluation cases to %s" % output_filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("input_files", type=str, nargs='+',
                        help="Input file(s). Linked articles with ground truth labels.")
    parser.add_argument("-o", "--output_file", type=str,
                        help="Output file for the evaluation results."
                             " The input file with .eval_cases.jsonl extension if none is specified.")
    parser.add_argument("--no_coreference", action="store_true",
                        help="Exclude coreference cases from the evaluation.")
    parser.add_argument("-b", "--benchmark", choices=get_available_benchmarks(),
                        help="Benchmark over which to evaluate the linked entities. If none is given,"
                             "labels and benchmark texts are retrieved from the given jsonl file.")
    parser.add_argument("-w", "--write_labels", action="store_true",
                        help="Write the labels of the provided benchmark to the input file.")
    parser.add_argument("--no-unknowns", action="store_true",
                        help="Set if the benchmark contains no 'unknown' labels. "
                             "Uppercase false detections will be treated as 'unknown named entity' errors.")
    parser.add_argument("--type_mapping", type=str,
                        help="Map groundtruth labels and predicted entities to types using the given mapping.")
    parser.add_argument("--type_whitelist", type=str,
                        help="Evaluate only over labels with a type from the given whitelist and ignore other labels. "
                             "One type per line in the format \"<qid> # <label>\".")
    parser.add_argument("--type_filter_predictions", action="store_true",
                        help="Ignore predicted links that do not have a type from the type whitelist."
                             "This has no effect if the type_whitelist argument is not provided.")
    parser.add_argument("-c", "--custom_mappings", action="store_true",
                        help="Use custom entity to name and entity to type mappings instead of Wikidata.")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    cmdl_args = parser.parse_args()

    if len(cmdl_args.input_files) > 1:
        if cmdl_args.output_file:
            parser.error('--output_file/-o is not a valid option when evaluating several input files at once.')

    main(cmdl_args)
