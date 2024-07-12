import argparse
import sys
import json
from datetime import datetime

from elevant import settings
from elevant.utils import log
from elevant.utils.colors import Colors
from elevant.evaluation.benchmark import BenchmarkFormat, Benchmark, get_available_benchmarks
from elevant.evaluation.benchmark_iterator import get_benchmark_iterator
from elevant.evaluation.groundtruth_label import GroundtruthLabel
from elevant.models.entity_database import EntityDatabase
from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper


def main(args):
    benchmark_info = args.benchmark if args.benchmark else args.benchmark_file
    logger.info(f"Transform benchmark {Colors.BLUE}{benchmark_info}{Colors.END} into jsonl format and annotate"
                f"groundtruth labels with Wikidata label and type.")

    from_json_file = args.benchmark in get_available_benchmarks()
    benchmark_arg = args.benchmark if args.benchmark else args.benchmark_name
    benchmark_iterator = get_benchmark_iterator(benchmark_arg,
                                                from_json_file=from_json_file,
                                                benchmark_files=args.benchmark_file,
                                                benchmark_format=args.benchmark_format,
                                                custom_kb=args.custom_kb)

    entity_db = EntityDatabase()
    if args.custom_kb:
        entity_db.load_custom_entity_names(settings.CUSTOM_ENTITY_TO_NAME_FILE)
        entity_db.load_custom_entity_types(settings.CUSTOM_ENTITY_TO_TYPES_FILE)
    else:
        entity_db.load_entity_names()
        entity_db.load_entity_types()

    lines_to_write = ""
    for article in benchmark_iterator.iterate():
        for label in article.labels:
            if KnowledgeBaseMapper.is_unknown_entity(label.entity_id):
                continue
            if label.type in (GroundtruthLabel.QUANTITY, GroundtruthLabel.DATETIME):
                continue

            label.type = "|".join(entity_db.get_entity_types(label.entity_id))
            label.name = entity_db.get_entity_name(label.entity_id)

        lines_to_write += article.to_json() + '\n'

    # Write to output file after reading everything from the input benchmark, since the input benchmark file
    # can be the same as the output file e.g. when an existing benchmark is annotated with new types / labels
    filename = settings.BENCHMARK_DIR + args.benchmark_name + ".benchmark.jsonl"
    metadata_filename = settings.BENCHMARK_DIR + args.benchmark_name + ".metadata.json"

    output_file = open(filename, "w", encoding="utf8")
    output_file.write(lines_to_write)
    output_file.close()

    with open(metadata_filename, "w", encoding="utf8") as metadata_file:
        description = args.description
        name = args.displayed_name if args.displayed_name else args.benchmark_name
        metadata = {"name": name,
                    "description": description,
                    "timestamp": datetime.now().strftime("%Y/%m/%d %H:%M")}
        metadata_file.write(json.dumps(metadata))
    logger.info(f"Wrote benchmark metadata to {Colors.BOLD}{metadata_filename}{Colors.END}")

    logger.info(f"Wrote benchmark articles to {Colors.BOLD}{filename}{Colors.END}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=__doc__)

    parser.add_argument("benchmark_name", type=str,
                        help="Name of the output benchmark. "
                             "The benchmark will be written to benchmarks/<name>.benchmark.jsonl")

    group_benchmark = parser.add_mutually_exclusive_group(required=True)
    group_benchmark.add_argument("-b", "--benchmark",
                                 choices=set([b.value for b in Benchmark] + get_available_benchmarks()),
                                 help="Benchmark to annotate / create labels for.")
    group_benchmark.add_argument("-bfile", "--benchmark_file", type=str, nargs='+',
                                 help="File that contains text and information about groundtruth labels."
                                      "For certain benchmark readers, e.g. the XML benchmark readers, several"
                                      "benchmark files are needed as input.")

    parser.add_argument("-bformat", "--benchmark_format", choices=[f.value for f in BenchmarkFormat],
                        default=BenchmarkFormat.OURS_JSONL.value,
                        help="Format of the specified benchmark file. Default: " + BenchmarkFormat.OURS_JSONL.value)

    parser.add_argument("--description", "-desc", type=str,
                        help="A description for the benchmark that will be stored in the metadata file and displayed "
                             "in the webapp.")
    parser.add_argument("--displayed_name", "-dname", type=str,
                        help="The benchmark name that will be stored in the metadata file and displayed in the webapp.")

    parser.add_argument("-c", "--custom_kb", action="store_true",
                        help="Use custom entity to name and entity to type mappings (instead of Wikidata mappings).")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main(parser.parse_args())
