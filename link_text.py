"""
Links entities in a given file to their Wikidata entry.
The linker pipeline consists of three main components:

    1) linker: use a NER system and a NED system to detect and link entity
       mentions to their Wikidata entry.
    2) coreference linker: link coreferences to their Wikidata entry.

For each component, you can choose between different linker variants or omit
the component from the pipeline.
The result is written to a given output file in jsonl format with one article
per line.

About 55GB of RAM are required when using the full linker pipeline.
"""

import argparse
import json
import os
import sys
import time
import multiprocessing

from elevant import settings
from elevant.utils import log
from elevant.linkers.linkers import Linkers, CoreferenceLinkers
from elevant.models.article import Article, article_from_json
from elevant.helpers.wikipedia_dump_reader import WikipediaDumpReader

# Don't show dependencygraph UserWarning: "The graph doesn't contain a node that depends on the root element."
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Importing the linking_system has to happen here, otherwise a linking_system is not defined error is thrown.
# In order to not load several GB of mappings twice, only do a fake loading such that the name is imported,
# but no mappings are loaded
config = {"no_loading": True}
with open(settings.TMP_FORKSERVER_CONFIG_FILE, "w", encoding="utf8") as config_file:
    json.dump(config, config_file)
from elevant.linkers.forkserver_linking_system import linking_system


CHUNK_SIZE = 10  # Number of articles submitted to one process as a single task
MAX_TASKS_PER_CHILD = 5


def link_entities_tuple_argument(args_tuple):
    """
    Helper function for ProcessPoolExecutor.map that takes a single argument.
    """
    linking_system.link_entities(args_tuple[0], args_tuple[1], args_tuple[2])
    return args_tuple[0]


def article_iterator(filename):
    with open(filename, 'r', encoding='utf8') as file:
        for i, line in enumerate(file):
            if i == args.n_articles:
                break
            if args.raw_input:
                article = Article(id=i, title="", text=line[:-1])
            elif args.article_format:
                article = article_from_json(line)
            else:
                article = WikipediaDumpReader.json2article(line)
            yield article, args.uppercase, args.only_pronouns


def main():
    logger.info("Linking entities in file %s" % args.input_file)

    out_dir = os.path.dirname(args.output_file)
    if out_dir and not os.path.exists(out_dir):
        logger.info("Creating directory %s" % out_dir)
        os.makedirs(out_dir)

    output_file = open(args.output_file, 'w', encoding='utf8')

    i = 0
    iterator = article_iterator(args.input_file)
    if args.multiprocessing > 1:
        logger.info("Loading linking system...")
        multiprocessing.set_start_method('forkserver')
        multiprocessing.set_forkserver_preload(["elevant.linkers.forkserver_linking_system"])
        start = time.time()
        last_time = start
        with multiprocessing.Pool(processes=args.multiprocessing, maxtasksperchild=MAX_TASKS_PER_CHILD) as executor:
            logger.info("Start linking using %d processes." % args.multiprocessing)
            for article in executor.imap(link_entities_tuple_argument, iterator, chunksize=CHUNK_SIZE):
                output_file.write(f"{article.to_json(evaluation_format=False)}\n")
                i += 1
                if i % 100 == 0:
                    total_time = time.time() - start
                    avg_time = total_time / i
                    avg_last_time = (time.time() - last_time) / 100
                    print(f"\r{i} articles, {avg_time:.5f} s per article, "
                          f"{avg_last_time:.2f} s per article for the last 100 articles, "
                          f"{int(total_time)} s total time.", end='')
                    last_time = time.time()
        i -= 1  # So final log reports correct number of linked articles with and without multiprocessing
    else:
        from elevant.linkers.linking_system import LinkingSystem
        ls = LinkingSystem(args.linker_name,
                           args.linker_config,
                           coref_linker=args.coreference_linker,
                           min_score=args.minimum_score,
                           type_mapping_file=args.type_mapping)
        logger.info("Start linking with a single process.")
        start = time.time()
        for i, tupl in enumerate(iterator):
            article, uppercase, only_pronouns = tupl
            ls.link_entities(article, uppercase, only_pronouns)
            output_file.write(f"{article.to_json(evaluation_format=False)}\n")
            total_time = time.time() - start
            time_per_article = total_time / (i + 1)
            print("\r%i articles, %f s per article, %f s total time." % (i + 1, time_per_article, total_time), end='')

    print()
    logger.info("Linked %d articles in %fs" % (i+1, time.time() - start))
    logger.info("Linked articles written to %s" % args.output_file)
    output_file.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=__doc__)

    parser.add_argument("input_file", type=str,
                        help="Input file with articles in JSON format or raw text.")
    parser.add_argument("output_file", type=str,
                        help="Output file.")
    parser.add_argument("-l", "--linker_name", choices=[li.value for li in Linkers], required=True,
                        help="Entity linker name.")
    parser.add_argument("--linker_config",
                        help="Configuration file for the specified linker."
                             "Per default, the system looks for the config file at configs/<linker_name>.config.json")
    parser.add_argument("-raw", "--raw_input", action="store_true",
                        help="Set to use an input file with raw text.")
    parser.add_argument("--article_format", action="store_true",
                        help="The input file is in our article jsonl format.")
    parser.add_argument("-n", "--n_articles", type=int, default=-1,
                        help="Number of articles to link.")
    parser.add_argument("-coref", "--coreference_linker", choices=[cl.value for cl in CoreferenceLinkers],
                        help="Coreference linker to apply after entity linkers.")
    parser.add_argument("--only_pronouns", action="store_true",
                        help="Only link coreferences that are pronouns.")
    parser.add_argument("-min", "--minimum_score", type=int, default=0,
                        help="Minimum entity score to include entity in database")
    parser.add_argument("--uppercase", action="store_true",
                        help="Set to remove all predictions on snippets which do not contain an uppercase character.")
    parser.add_argument("--type_mapping", type=str, default=settings.QID_TO_WHITELIST_TYPES_DB,
                        help="For pure prior linker: Map predicted entities to types using the given mapping.")
    parser.add_argument("-m", "--multiprocessing", type=int, default=1,
                        help="Number of processes to use. Default is 1, i.e. no multiprocessing.")

    args = parser.parse_args()

    # Don't write the log output to a file as the logger does usually.
    # Otherwise, a FileNotFoundError is thrown.
    logger = log.setup_logger(sys.argv[0], write_to_file=False)
    logger.debug(' '.join(sys.argv))

    # Write command line arguments to temporary config file which is then read by the forkserver_linking_system module.
    # This is not mega pretty, but I don't see a better solution where the user can still use command line arguments to
    # configure the linking_system.
    config = {"linker_name": args.linker_name,
              "linker_config": args.linker_config,
              "coreference_linker": args.coreference_linker,
              "minimum_score": args.minimum_score,
              "type_mapping": args.type_mapping}
    with open(settings.TMP_FORKSERVER_CONFIG_FILE, "w", encoding="utf8") as config_file:
        json.dump(config, config_file)

    main()
