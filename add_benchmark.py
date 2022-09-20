import argparse
import log
import sys

from src import settings
from src.evaluation.benchmark import BenchmarkFormat, Benchmark, get_available_benchmarks
from src.evaluation.examples_generator import get_example_generator
from src.evaluation.groundtruth_label import GroundtruthLabel
from src.helpers.entity_database_reader import EntityDatabaseReader


def main(args):
    benchmark_info = args.benchmark if args.benchmark else args.benchmark_file
    logger.info("Transform benchmark %s into jsonl format and annotate groundtruth labels with Wikidata label and type."
                % benchmark_info)

    from_json_file = args.benchmark in get_available_benchmarks()
    example_iterator = get_example_generator(args.benchmark,
                                             from_json_file=from_json_file,
                                             benchmark_file=args.benchmark_file,
                                             benchmark_format=args.benchmark_format)

    label_entity_ids = set()
    for article in example_iterator.iterate():
        for label in article.labels:
            label_entity_ids.add(label.entity_id)

    logger.info("Loading entity information..")
    entities = EntityDatabaseReader.get_wikidata_entities_with_types(label_entity_ids, settings.WHITELIST_TYPE_MAPPING)

    lines_to_write = ""
    for article in example_iterator.iterate():
        for label in article.labels:
            if label.entity_id.startswith("Unknown"):
                continue
            if label.type in (GroundtruthLabel.QUANTITY, GroundtruthLabel.DATETIME):
                continue

            if label.entity_id in entities:
                label.type = entities[label.entity_id].type
            else:
                logger.warning("Entity %s:%s was not found in entity-type mapping." % (label.entity_id, label.name))

            label.name = entities[label.entity_id].name if label.entity_id in entities else "Unknown"

        lines_to_write += article.to_json() + '\n'

    # Write to output file after reading everything from the input benchmark, since the input benchmark file
    # can be the same as the output file e.g. when an existing benchmark is annotated with new types / labels
    if args.output_benchmark_name:
        filename = settings.BENCHMARK_DIR + args.output_benchmark_name + ".benchmark.jsonl"
    else:
        filename = args.output_file
    output_file = open(filename, "w", encoding="utf8")
    output_file.write(lines_to_write)
    output_file.close()
    logger.info("Wrote new articles to %s" % filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=__doc__)

    group_output = parser.add_mutually_exclusive_group(required=True)
    group_output.add_argument("-name", "--output_benchmark_name", type=str,
                              help="Name of the output benchmark."
                                   "The benchmark will be written to benchmarks/<name>.benchmark.jsonl")
    group_output.add_argument("-o", "--output_file", type=str,
                              help="The benchmark will be written to the specified file.")

    group_benchmark = parser.add_mutually_exclusive_group(required=True)
    group_benchmark.add_argument("-b", "--benchmark",
                                 choices=set([b.value for b in Benchmark] + get_available_benchmarks()),
                                 help="Benchmark to annotate / create labels for.")
    group_benchmark.add_argument("-bfile", "--benchmark_file", type=str,
                                 help="File that contains text and information about groundtruth labels")

    parser.add_argument("-bformat", "--benchmark_format", choices=[f.value for f in BenchmarkFormat],
                        default=BenchmarkFormat.OURS_JSONL.value,
                        help="Format of the specified benchmark file. Default: " + BenchmarkFormat.OURS_JSONL.value)

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main(parser.parse_args())
