"""
Evaluates entity linking.
This takes a jsonl file produced by link_benchmark.py with one linked
article and its ground truth labels per line.
The resulting evaluation cases are written to an output file in jsonl format
with one case per line.
The evaluation results are printed.
"""

import argparse
import sys
import json
import re

from elevant import settings
from elevant.utils import log
from elevant.utils.colors import Colors
from elevant.evaluation.benchmark import get_available_benchmarks
from elevant.evaluation.benchmark_iterator import get_benchmark_iterator
from elevant.models.article import article_from_json
from elevant.evaluation.evaluator import Evaluator
from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper


def main(args):
    logger.info(f"Evaluating linking results from {Colors.BLUE}{args.input_files}{Colors.END} ...")

    # Read whitelist types for filtering labels
    label_whitelist_types = set()
    if args.filter_labels_with_whitelist:
        with open(args.filter_labels_with_whitelist, 'r', encoding='utf8') as file:
            for line in file:
                type_match = re.search(r"Q[0-9]+", line)
                if type_match:
                    typ = type_match.group(0)
                    label_whitelist_types.add(typ)

    # Read whitelist types for filtering predictions
    prediction_whitelist_types = set()
    if args.filter_predictions_with_whitelist:
        with open(args.filter_predictions_with_whitelist, 'r', encoding='utf8') as file:
            for line in file:
                type_match = re.search(r"Q[0-9]+", line)
                if type_match:
                    typ = type_match.group(0)
                    prediction_whitelist_types.add(typ)

    whitelist_file = settings.WHITELIST_FILE
    if args.custom_kb:
        whitelist_file = settings.CUSTOM_WHITELIST_TYPES_FILE

    type_mapping_file = args.type_mapping if args.type_mapping else settings.QID_TO_WHITELIST_TYPES_DB
    evaluator = Evaluator(type_mapping_file, whitelist_file=whitelist_file, contains_unknowns=not args.no_unknowns,
                          custom_kb=args.custom_kb)

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
            logger.info(f"Retrieving labels from {args.benchmark} benchmark file instead of {input_file_name}")
            benchmark_iterator = get_benchmark_iterator(args.benchmark).iterate()

        logger.info(f"Evaluating linking results from {Colors.BLUE}{input_file_name}{Colors.END}")
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

            # If the filter_labels_with_whitelist argument is set, ignore groundtruth labels that
            # do not have a type that is included in the whitelist
            if args.filter_labels_with_whitelist:
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
                            if typ in label_whitelist_types or gt_label.parent is not None \
                                    or KnowledgeBaseMapper.is_unknown_entity(gt_label.entity_id):
                                filtered_labels.append(gt_label)
                                added_label_ids.add(gt_label.id)
                                break
                article.labels = filtered_labels

            # If the filter_predictions_with_whitelist argument is set, ignore predictions that do
            # not have a type that is included in the whitelist
            if args.filter_predictions_with_whitelist:
                filtered_entity_mentions = {}
                for span, em in article.entity_mentions.items():
                    types = evaluator.entity_db.get_entity_types(em.entity_id)
                    for typ in types:
                        if typ in prediction_whitelist_types:
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
        logger.info(f"Wrote results to {Colors.BOLD}{results_file}{Colors.END}")

        if args.benchmark and args.write_benchmark:
            input_file.seek(0)
            input_file_lines = input_file.readlines()
            input_file.close()
            with open(input_file_name, 'w', encoding='utf8') as file:
                benchmark_iterator = get_benchmark_iterator(args.benchmark).iterate()
                for line in input_file_lines:
                    article = article_from_json(line)
                    benchmark_article = next(benchmark_iterator)
                    article.labels = benchmark_article.labels
                    article.title = benchmark_article.title
                    article.text = benchmark_article.text
                    file.write(article.to_json() + "\n")
        else:
            input_file.close()

        output_file.close()
        logger.info(f"Wrote evaluation cases to {Colors.BOLD}{output_filename}{Colors.END}")


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
    parser.add_argument("-w", "--write_benchmark", action="store_true",
                        help="Write the labels, article title and text of the provided benchmark to the input file.")
    parser.add_argument("--no-unknowns", action="store_true",
                        help="Set if the benchmark contains no 'unknown' labels. "
                             "Uppercase false detections will be treated as 'unknown named entity' errors.")
    parser.add_argument("--type_mapping", type=str,
                        help="Map groundtruth labels and predicted entities to types using the given mapping.")
    parser.add_argument("-flw", "--filter_labels_with_whitelist", type=str,
                        help="Evaluate only over labels with a type from the given whitelist and ignore other labels. "
                             "One type per line in the format \"<qid> # <label>\".")
    parser.add_argument("-fpw", "--filter_predictions_with_whitelist", type=str,
                        help="Ignore predicted links that do not have a type from the provided type whitelist.")
    parser.add_argument("-c", "--custom_kb", action="store_true",
                        help="Use custom entity to name and entity to type mappings (instead of Wikidata mappings).")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    cmdl_args = parser.parse_args()

    if len(cmdl_args.input_files) > 1:
        if cmdl_args.output_file:
            parser.error('--output_file/-o is not a valid option when evaluating several input files at once.')

    main(cmdl_args)
