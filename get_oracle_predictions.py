import argparse

from src.evaluation.benchmark import Benchmark
from src.evaluation.examples_generator import get_example_generator
from src.models.entity_prediction import EntityPrediction


def main(args):
    example_generator = get_example_generator(args.benchmark)

    output_file = open(args.output_file, 'w', encoding='utf8')

    for i, article in enumerate(example_generator.iterate()):
        predicted_entities = dict()
        for gt_label in article.labels:
            # Only include non-optional (no optionals, quantities or datetimes), known root gt labels in the predictions
            if gt_label.parent is None and not gt_label.is_optional() and not gt_label.entity_id.startswith("Unknown"):
                predicted_entities[gt_label.span] = EntityPrediction(gt_label.span, gt_label.entity_id,
                                                                     {gt_label.entity_id})
        article.link_entities(predicted_entities, "ORACLE", "ORACLE")
        output_file.write(article.to_json() + '\n')

    print("Wrote linked articles to %s" % args.output_file)
    output_file.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("output_file", type=str,
                        help="Output file for the oracle predictions.")
    parser.add_argument("-b", "--benchmark", choices=[b.value for b in Benchmark], default=None,
                        help="Benchmark over which to evaluate the linked entities. If none is given, labels are"
                             "retrieved from the given jsonl file")

    main(parser.parse_args())
