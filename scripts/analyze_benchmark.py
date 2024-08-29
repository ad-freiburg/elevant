import argparse
import sys
import json
import spacy

from elevant import settings
from elevant.utils import log
from elevant.evaluation.benchmark import get_available_benchmarks
from elevant.evaluation.benchmark_statistics import BenchmarkStatistics
from elevant.utils.colors import Colors

from elevant.models.entity_database import EntityDatabase


def load_entity_database():
    entity_db = EntityDatabase()
    entity_db.load_entity_names()
    entity_db.load_entity_types()
    entity_db.load_demonyms()
    entity_db.load_quantities()
    entity_db.load_datetimes()
    entity_db.load_family_name_aliases()
    entity_db.load_alias_to_entities()
    entity_db.load_hyperlink_to_most_popular_candidates()
    return entity_db


def main(args):
    model = spacy.load("en_core_web_lg")
    entity_db = load_entity_database()
    benchmarks = get_available_benchmarks() if "ALL" in args.benchmark else args.benchmark
    for i, benchmark in enumerate(benchmarks):
        stats = BenchmarkStatistics(entity_db, model)
        benchmark_cases = stats.analyze_benchmark(benchmark, args.only_root_labels)
        json_string = ""
        for article_cases in benchmark_cases:
            json_string += json.dumps([case.to_dict() for case in article_cases])
            json_string += "\n"

        # Write the benchmark cases and statistics to an output file
        if args.output_file:
            filename = args.output_file[i]
        else:

            root = "-root" if args.only_root_labels else ""
            filename = settings.BENCHMARK_DIR + benchmark + root + ".benchmark_statistics.jsonl"

        output_file = open(filename, "w", encoding="utf8")
        output_file.write(stats.to_json() + "\n" + json_string)
        output_file.close()

        logger.info(f"Wrote benchmark statistics to {Colors.BOLD}{filename}{Colors.END}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("-b", "--benchmark", choices=get_available_benchmarks() + ["ALL"], nargs='+', required=True,
                        help="Benchmark(s) to analyze.")
    parser.add_argument("-o", "--output_file", type=str, nargs='+',
                        help="Output file for the benchmark statistics. If none is specified, this is "
                             "the benchmark name with .benchmark_statistics.jsonl extension. The number of "
                             "output files must match the number of benchmarks.")
    parser.add_argument("-root", "--only_root_labels", action="store_true",
                        help="Only include root labels in the analysis and ignore child labels.")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    cmdl_args = parser.parse_args()

    # Make sure the number of output files matches the number of benchmarks
    if cmdl_args.output_file and len(cmdl_args.output_file) != len(cmdl_args.benchmark):
        logger.error("The number of output files must match the number of benchmarks.")
        sys.exit(1)

    main(cmdl_args)
