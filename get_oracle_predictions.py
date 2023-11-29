import argparse
import log
import sys

from src.evaluation.benchmark import get_available_benchmarks
from src.evaluation.benchmark_iterator import get_benchmark_iterator
from src.evaluation.groundtruth_label import GroundtruthLabel
from src.models.entity_prediction import EntityPrediction


def get_label(gt_label: GroundtruthLabel):
    entity_id = gt_label.entity_id
    if entity_id.startswith("Unknown"):
        entity_id = None
    return EntityPrediction(gt_label.span, entity_id, {entity_id})


def main(args):
    logger.info("Generating oracle links for %s ..." % args.benchmark)

    benchmark_iterator = get_benchmark_iterator(args.benchmark, benchmark_files=args.benchmark_file)

    output_file = open(args.output_file, 'w', encoding='utf8')

    for i, article in enumerate(benchmark_iterator.iterate()):
        predicted_entities = dict()
        label_dict = {gt_label.id: gt_label for gt_label in article.labels}
        for gt_label in article.labels:
            # Only include non-optional (no optionals, descriptives, quantities or datetimes)
            # root gt labels in the predictions
            # or non-optional child gt labels with optional parents.
            if gt_label.parent is None:
                if not gt_label.is_optional():
                    predicted_entities[gt_label.span] = get_label(gt_label)
                elif gt_label.has_non_optional_child(label_dict):
                    # Due to this part, it is now not enough anymore to count the number of oracle
                    # predictions on our benchmarks to find out the number of parent labels.
                    child_ids = gt_label.children[:]
                    while len(child_ids) > 0:
                        child_id = child_ids.pop()
                        child_label = label_dict[child_id]
                        if not child_label.is_optional():
                            predicted_entities[child_label.span] = get_label(child_label)
                        elif child_label.has_non_optional_child(label_dict):
                            child_ids.extend(child_label.children)

        article.link_entities(predicted_entities, "ORACLE", "ORACLE")
        output_file.write(article.to_json() + '\n')

    logger.info("Wrote articles with oracle links to %s" % args.output_file)
    output_file.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("output_file", type=str,
                        help="Output file for the oracle predictions.")

    group_benchmark = parser.add_mutually_exclusive_group(required=True)
    group_benchmark.add_argument("-b", "--benchmark", choices=get_available_benchmarks(),
                                 help="Name of the benchmark over which to evaluate the linked entities.")
    group_benchmark.add_argument("-bfile", "--benchmark_file", type=str, nargs="+",
                                 help="Benchmark file over which to evaluate the linked entities.")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main(parser.parse_args())
