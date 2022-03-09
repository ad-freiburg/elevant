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
from src.evaluation.case import case_from_dict
from src.evaluation.examples_generator import get_example_generator
from src.models.article import article_from_json
from src.evaluation.evaluator import Evaluator


def main(args):
    logger.info("Evaluating linking results from %s ..." % args.input_file)
    input_file = open(args.input_file, 'r', encoding='utf8')
    idx = args.input_file.rfind('.')

    output_file = None
    case_file = None
    output_filename = None

    # Get a set of entity ids of all predicted entities and candidate entities
    # to load their information into the entity_db
    # (all necessary information about ground truth labels is already contained in the benchmark jsonl file)
    logger.info("Extracting relevant entities (predicted entities, candidates and "
                "groundtruth entities if a type mapping is given) ...")
    relevant_entity_ids = set()
    for line in input_file:
        article = article_from_json(line)
        for em in article.entity_mentions.values():
            relevant_entity_ids.add(em.entity_id)
            relevant_entity_ids.update(em.candidates)
        if args.type_mapping and not args.benchmark:
            # If a type mapping other than the default mapping is used, ground truth labels must be re-annotated
            for gt_label in article.labels:
                relevant_entity_ids.add(gt_label.entity_id)
    if args.type_mapping and args.benchmark:
        for article in get_example_generator(args.benchmark).iterate():
            for gt_label in article.labels:
                relevant_entity_ids.add(gt_label.entity_id)

    # Read whitelist types
    whitelist_types = set()
    if args.type_whitelist:
        with open(args.type_whitelist, 'r', encoding='utf8') as file:
            for line in file:
                type_match = re.search(r"Q[0-9]+", line)
                if type_match:
                    type = type_match.group(0)
                    whitelist_types.add(type)

    whitelist_file = args.type_whitelist if args.type_whitelist else settings.WHITELIST_FILE
    if args.input_case_file:
        logger.info("Using cases from %s" % args.input_case_file)
        case_file = open(args.input_case_file, 'r', encoding='utf8')
        evaluator = Evaluator(relevant_entity_ids, None, whitelist_file=whitelist_file, load_data=False,
                              coreference=not args.no_coreference, contains_unknowns=not args.no_unknowns)
    else:
        type_mapping_file = args.type_mapping if args.type_mapping else settings.WHITELIST_TYPE_MAPPING
        evaluator = Evaluator(relevant_entity_ids, type_mapping_file, whitelist_file=whitelist_file, load_data=True,
                              contains_unknowns=not args.no_unknowns)
        output_filename = args.output_file if args.output_file else args.input_file[:idx] + ".cases"
        output_file = open(output_filename, 'w', encoding='utf8')
    results_file = (args.output_file[:-6] if args.output_file else args.input_file[:idx]) + ".results"

    example_iterator = None
    if args.benchmark:
        # If a benchmark is given, labels are retrieved from the benchmark
        # and not from the given jsonl file. The user has to make sure the files match.
        logger.info("Retrieving labels from %s benchmark file instead of %s" % (args.benchmark, args.input_file))
        example_iterator = get_example_generator(args.benchmark).iterate()

    logger.info("Evaluating linked entities ...")
    input_file.seek(0)
    for line in input_file:
        article = article_from_json(line)
        if example_iterator:
            benchmark_article = next(example_iterator)
            article.labels = benchmark_article.labels

        if args.type_mapping:
            # Map benchmark label entities to types in the mapping
            for gt_label in article.labels:
                entity = evaluator.entity_db.get_entity(gt_label.entity_id)
                if entity:  # Should be None only if label is a Unknown, but for some reason it doesn't happen
                    gt_label.type = entity.type

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
                    types = gt_label.type.split("|")
                    for type in types:
                        if type in whitelist_types or gt_label.parent is not None \
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
                    types = evaluator.entity_db.get_entity(em.entity_id).type.split("|")
                    for type in types:
                        if type in whitelist_types:
                            filtered_entity_mentions[span] = em
                            break
                article.entity_mentions = filtered_entity_mentions

        if args.input_case_file:
            dump = json.loads(case_file.readline())
            cases = [case_from_dict(case_dict) for case_dict in dump]
        else:
            cases = evaluator.get_cases(article)
        evaluator.add_cases(cases)

        if not args.input_case_file:
            case_list = [case.to_dict() for case in cases]
            output_file.write(json.dumps(case_list) + "\n")

    results_dict = evaluator.get_results_dict()
    evaluator.print_results()
    with open(results_file, "w") as f:
        f.write(json.dumps(results_dict))
    logger.info("Wrote results to %s" % results_file)

    input_file.close()
    if args.input_case_file:
        case_file.close()
    else:
        output_file.close()
        logger.info("Wrote evaluation cases to %s" % output_filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("input_file", type=str,
                        help="Input file. Linked articles with ground truth labels.")
    parser.add_argument("-o", "--output_file", type=str,
                        help="Output file for the evaluation results."
                             " The input file with .cases extension if none is specified.")
    parser.add_argument("-icf", "--input_case_file", type=str,
                        help="Input file that contains the evaluation cases. Cases are not written to file.")
    parser.add_argument("--no_coreference", action="store_true",
                        help="Exclude coreference cases from the evaluation.")
    parser.add_argument("-b", "--benchmark", choices=get_available_benchmarks(),
                        help="Benchmark over which to evaluate the linked entities. If none is given, labels are"
                             "retrieved from the given jsonl file")
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

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main(parser.parse_args())
