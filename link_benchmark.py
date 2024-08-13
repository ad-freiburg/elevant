"""
Links entities in a specified benchmark to their Wikidata entry.
The linker pipeline consists of two main components:

    1) linker: use a NER system and a NED system to detect and link remaining
       entity mentions.
    2) coreference linker: link coreferences to their Wikidata entry.

For each component, you can choose between different linker variants or omit
the component from the pipeline.
The result is written to a given output file in jsonl format with one article
per line.
"""

import argparse
import sys
import os
import json
import time
from datetime import datetime
from tqdm import tqdm

from elevant import settings
from elevant.utils import log
from elevant.utils.colors import Colors
from elevant.evaluation.benchmark import get_available_benchmarks
from elevant.evaluation.benchmark_iterator import get_benchmark_iterator
from elevant.linkers.linkers import Linkers, CoreferenceLinkers, PredictionFormats
from elevant.linkers.linking_system import LinkingSystem
from elevant.linkers.oracle_linker import link_entities_with_oracle
from elevant.utils.utils import convert_to_filename


def main(args):
    linking_system = None
    if not args.linker_name == "oracle":
        linking_system = LinkingSystem(args.linker_name,
                                       args.linker_config,
                                       args.prediction_file,
                                       args.prediction_format,
                                       args.prediction_name,
                                       args.coreference_linker,
                                       args.minimum_score,
                                       args.type_mapping,
                                       args.custom_kb,
                                       args.api_url)

    benchmarks = get_available_benchmarks() if "ALL" in args.benchmark else args.benchmark

    for benchmark in benchmarks:
        benchmark_iterator = get_benchmark_iterator(benchmark)

        prediction_name_dir = convert_to_filename(args.prediction_name)
        linker_dir = args.linker_name if args.linker_name else prediction_name_dir
        output_dir = args.evaluation_dir.rstrip("/") + "/" + linker_dir
        experiment_filename = convert_to_filename(args.experiment_name)
        output_filename = output_dir + "/" + experiment_filename + "." + benchmark + ".linked_articles.jsonl"
        metadata_filename = output_filename[:-len(".linked_articles.jsonl")] + ".metadata.json"
        if output_dir and not os.path.exists(output_dir):
            logger.info(f"Creating directory {output_dir}")
            os.makedirs(output_dir)

        output_file = open(output_filename, 'w', encoding='utf8')

        logger.info(f"Linking entities in {Colors.BLUE}{benchmark}{Colors.END} benchmark ...")

        n_articles = 0
        start_time = time.time()
        for i, article in enumerate(tqdm(benchmark_iterator.iterate(), desc="Linking progress", unit=" articles")):
            evaluation_span = article.evaluation_span if args.evaluation_span else None
            if args.linker_name == "oracle":
                link_entities_with_oracle(article)
            else:
                linking_system.link_entities(article, args.uppercase, args.only_pronouns, evaluation_span)
            output_file.write(article.to_json() + '\n')
            n_articles = i+1
        linking_time = time.time() - start_time

        output_file.close()

        # Write metadata to metadata file
        with open(metadata_filename, "w", encoding="utf8") as metadata_file:
            linker_config = linking_system.get_linker_config() if linking_system else {}
            exp_name = args.experiment_name
            exp_description = None
            if args.description:
                exp_description = args.description
            elif "experiment_description" in linker_config:
                exp_description = linker_config["experiment_description"]
            linker_name = None
            if "linker_name" in linker_config:
                linker_name = linker_config["linker_name"]
            elif args.linker_name:
                linker_name = args.linker_name
            elif args.prediction_name:
                linker_name = args.prediction_name
            metadata = {"experiment_name": exp_name,
                        "experiment_description": exp_description,
                        "linker_name": linker_name,
                        "timestamp": datetime.now().strftime("%Y/%m/%d %H:%M"),
                        "linking_time": linking_time if args.linker_name else None}
            metadata_file.write(json.dumps(metadata))

        logger.info(f"Wrote metadata to {Colors.BOLD}{metadata_filename}{Colors.END}")
        logger.info(f"Wrote {n_articles} linked articles to {Colors.BOLD}{output_filename}{Colors.END}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("experiment_name", type=str,
                        help="Name for the resulting file. The linking results will be written to "
                             "<evaluation_dir>/<linker_name>/<experiment_name>.<benchmark_name>.linked_articles.jsonl")

    linker_group = parser.add_mutually_exclusive_group(required=True)
    linker_group.add_argument("-l", "--linker_name", choices=[li.value for li in Linkers] + ["oracle"],
                              help="Entity linker name.")
    linker_group.add_argument("-pfile", "--prediction_file",
                              help="Path to predictions file.")
    linker_group.add_argument("-api", "--api_url", type=str,
                              help="URL of the linker API that will be used to link entities.")

    parser.add_argument("--linker_config",
                        help="Configuration file for the specified linker."
                             "Per default, the system looks for the config file at configs/<linker_name>.config.json")
    parser.add_argument("-pformat", "--prediction_format", choices=[pf.value for pf in PredictionFormats],
                        help="Format of the prediction file.")
    parser.add_argument("-pname", "--prediction_name", default="Unknown Linker",
                        help="Name of the system that produced the predictions.")

    parser.add_argument("-b", "--benchmark", choices=get_available_benchmarks() + ["ALL"], required=True, nargs='+',
                        help="Benchmark(s) over which to evaluate the linker.")
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
    parser.add_argument("--uppercase", action="store_true",
                        help="Set to remove all predictions on snippets which do not contain an uppercase character.")
    parser.add_argument("--type_mapping", type=str, default=settings.QID_TO_WHITELIST_TYPES_DB,
                        help="For pure prior linker: Map predicted entities to types using the given mapping.")

    parser.add_argument("--description", "-desc", type=str,
                        help="A description for the experiment. This will be displayed in the webapp.")
    parser.add_argument("-c", "--custom_kb", action="store_true",
                        help="Use custom entity to name and entity to type mappings (instead of Wikidata mappings).")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    cmdl_args = parser.parse_args()
    if cmdl_args.prediction_file and cmdl_args.prediction_format is None:
        parser.error("--prediction_file requires --prediction_format.")

    if ("ALL" in cmdl_args.benchmark or len(cmdl_args.benchmark) > 1) and cmdl_args.prediction_file:
        # Since otherwise one would have to provide multiple pfiles as well and those would
        # have to be provided in the exact order of the benchmarks. User errors could easily happen.
        # Also, the structure of linking system would have to be changed, since it currently takes a
        # prediction file upon initialization.
        parser.error('--prediction_file/-pfile is not supported when linking multiple benchmarks at once.')

    main(cmdl_args)
