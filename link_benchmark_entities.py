"""
Links entities in a specified benchmark to their WikiData entry.
The linker pipeline consists of three main components:

    1) link linker: use intra-Wikipedia links to detect entity mentions and
       link them to their WikiData entry.
    2) linker: use a NER system and a NED system to detect and link remaining
       entity mentions.
    3) coreference linker: link coreferences to their WikiData entry.

For each component, you can choose between different linker variants or omit
the component from the pipeline.
The result is written to a given output file in jsonl format with one article
per line.
"""

import argparse
import log
import sys
import os

from src import settings
from src.evaluation.benchmark import get_available_benchmarks
from src.linkers.linkers import Linkers, CoreferenceLinkers, PredictionFormats
from src.linkers.linking_system import LinkingSystem
from src.evaluation.examples_generator import get_example_generator


def main(args):
    linking_system = LinkingSystem(args.linker_name,
                                   args.linker_config,
                                   args.prediction_file,
                                   args.prediction_format,
                                   args.prediction_name,
                                   args.coreference_linker,
                                   args.minimum_score,
                                   args.type_mapping)

    example_generator = get_example_generator(args.benchmark)

    prediction_name_dir = "".join(c if c.isalnum() else "_" for c in args.prediction_name.lower())
    linker_dir = args.linker_name if args.linker_name else prediction_name_dir
    output_dir = args.evaluation_dir + linker_dir
    output_filename = output_dir + "/" + args.experiment_name + "." + args.benchmark + ".jsonl"
    if output_dir and not os.path.exists(output_dir):
        logger.info("Creating directory %s" % output_dir)
        os.makedirs(output_dir)

    output_file = open(output_filename, 'w', encoding='utf8')

    logger.info("Linking entities in %s benchmark ..." % args.benchmark)

    for i, article in enumerate(example_generator.iterate()):
        evaluation_span = article.evaluation_span if args.evaluation_span else None
        linking_system.link_entities(article, args.uppercase, args.only_pronouns, evaluation_span)
        output_file.write(article.to_json() + '\n')
        print("\r%i articles" % (i + 1), end='')
    print()

    output_file.close()

    logger.info("Wrote %d linked articles to %s" % (i+1, output_filename))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("experiment_name", type=str,
                        help="Name for the resulting file. The linking results will be written to "
                             "<evaluation_dir>/<linker_name>/<experiment_name>.<benchmark_name>.jsonl")

    linker_group = parser.add_mutually_exclusive_group(required=True)
    linker_group.add_argument("-l", "--linker_name", choices=[li.value for li in Linkers],
                              help="Entity linker name.")
    linker_group.add_argument("-pfile", "--prediction_file",
                              help="Path to predictions file.")

    parser.add_argument("--linker_config",
                        help="Configuration file for the specified linker."
                             "Per default, the system looks for the config file at configs/<linker_name>.config.json")
    parser.add_argument("-pformat", "--prediction_format", choices=[pf.value for pf in PredictionFormats],
                        help="Format of the prediction file.")
    parser.add_argument("-pname", "--prediction_name", default="Unknown Linker",
                        help="Name of the system that produced the predictions.")

    parser.add_argument("-b", "--benchmark", choices=get_available_benchmarks(), required=True,
                        help="Benchmark over which to evaluate the linker.")
    parser.add_argument("-dir", "--evaluation_dir", default=settings.EVALUATION_RESULTS_DIR,
                        help="Directory to which the evaluation result files are written.")
    parser.add_argument("-coref", "--coreference_linker", choices=[cl.value for cl in CoreferenceLinkers],
                        help="Coreference linker to apply after entity linkers.")
    parser.add_argument("--only_pronouns", action="store_true",
                        help="Only link coreferences that are pronouns.")
    parser.add_argument("--evaluation_span", action="store_true",
                        help="If specified, let coreference linker refer only to entities within the evaluation span")
    parser.add_argument("-min", "--minimum_score", type=int, default=0,
                        help="Minimum entity score to include entity in database")
    parser.add_argument("-small", "--small_database", action="store_true",
                        help="Load a small version of the database")
    parser.add_argument("--uppercase", action="store_true",
                        help="Set to remove all predictions on snippets which do not contain an uppercase character.")
    parser.add_argument("--type_mapping", type=str, default=settings.WHITELIST_TYPE_MAPPING,
                        help="For pure prior linker: Map predicted entities to types using the given mapping.")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    cmdl_args = parser.parse_args()
    if cmdl_args.prediction_file and cmdl_args.prediction_format is None:
        parser.error("--prediction_file requires --prediction_format.")

    main(cmdl_args)
