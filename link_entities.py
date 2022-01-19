"""
Links entities in a given file to their WikiData entry.
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
import os
import sys
import time

import log

from src import settings
from src.linkers.linkers import Linkers, LinkLinkers, CoreferenceLinkers
from src.linkers.linking_system import LinkingSystem
from src.models.wikipedia_article import WikipediaArticle
from src.helpers.wikipedia_dump_reader import WikipediaDumpReader
from src.models.neural_net import NeuralNet

import multiprocessing

CHUNK_SIZE = 10  # Number of articles submitted to one process as a single task
MAX_TASKS_PER_CHILD = 1


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
                article = WikipediaArticle(id=i, title="", text=line[:-1], links=[])
            else:
                article = WikipediaDumpReader.json2article(line)
            yield article, args.uppercase, args.only_pronouns


def main():
    if args.coreference_linker == "wexea" and not args.linker_type == "wexea":
        logger.warning("Wexea can only be used as coreference linker in combination with the Wexea linker")
        exit(1)

    logger.info("Linking entities in file %s" % args.input_file)

    out_dir = os.path.dirname(args.output_file)
    if out_dir and not os.path.exists(out_dir):
        logger.info("Creating directory %s" % out_dir)
        os.makedirs(out_dir)

    output_file = open(args.output_file, 'w', encoding='utf8')

    logger.info("Start linking using %d processes." % args.multiprocessing)
    start = time.time()
    iterator = article_iterator(args.input_file)
    i = 0
    if args.multiprocessing > 1:
        with multiprocessing.Pool(processes=args.multiprocessing, maxtasksperchild=MAX_TASKS_PER_CHILD) as executor:
            for article in executor.imap(link_entities_tuple_argument, iterator, chunksize=CHUNK_SIZE):
                output_file.write(article.to_json() + "\n")
                total_time = time.time() - start
                time_per_article = total_time / (i + 1)
                if (i + 1) % 100 == 0:
                    print("\r%i articles, %f s per article, %f s total time." %
                          (i + 1, time_per_article, total_time), end='')
                i += 1
            i -= 1  # So final log reports correct number of linked articles with and without multiprocessing
    else:
        for i, tupl in enumerate(iterator):
            article, uppercase, only_pronouns = tupl
            linking_system.link_entities(article, uppercase, only_pronouns)
            output_file.write(article.to_json() + "\n")
            total_time = time.time() - start
            time_per_article = total_time / (i + 1)
            print("\r%i articles, %f s per article, %f s total time." % (i + 1, time_per_article, total_time), end='')

    print()
    logger.info("Linked %d articles in %fs" % (i+1, time.time() - start))
    logger.info("Linked articles written to %s" % args.output_file)
    output_file.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=__doc__)

    parser.add_argument("input_file", type=str, default=None,
                        help="Input file with articles in JSON format or raw text.")
    parser.add_argument("output_file", type=str, default=None,
                        help="Output file.")
    parser.add_argument("linker_type", choices=[li.value for li in Linkers],
                        help="Entity linker type.")
    parser.add_argument("linker",
                        help="Specify the linker to be used, depending on its type:\n"
                        "BASELINE: Choose baseline from {scores, links, links-all, max-match-ner}.\n"
                        "SPACY: Name of the linker.\n"
                        "EXPLOSION: Full path to the saved model.\n"
                        "AMBIVERSE: Full path to the predictions directory (for Wikipedia or own benchmark only).\n"
                        "IOB: Full path to the prediction file in IOB format (for CoNLL benchmark only).\n")
    parser.add_argument("-raw", "--raw_input", action="store_true",
                        help="Set to use an input file with raw text.")
    parser.add_argument("-n", "--n_articles", type=int, default=-1,
                        help="Number of articles to link.")
    parser.add_argument("-kb", "--kb_name", type=str, choices=["wikipedia"], default=None,
                        help="Name of the knowledge base to use with a spacy linker.")
    parser.add_argument("-ll", "--link_linker", choices=[ll.value for ll in LinkLinkers], default=None,
                        help="Link linker to apply before spacy or explosion linker")
    parser.add_argument("-coref", "--coreference_linker", choices=[cl.value for cl in CoreferenceLinkers], default=None,
                        help="Coreference linker to apply after entity linkers.")
    parser.add_argument("--only_pronouns", action="store_true",
                        help="Only link coreferences that are pronouns.")
    parser.add_argument("-min", "--minimum_score", type=int, default=0,
                        help="Minimum entity score to include entity in database")
    parser.add_argument("-small", "--small_database", action="store_true",
                        help="Load a small version of the database")
    parser.add_argument("--longest_alias_ner", action="store_true",
                        help="For the baselines: use longest matching alias NER instead of SpaCy NER.")
    parser.add_argument("--uppercase", action="store_true",
                        help="Set to remove all predictions on snippets which do not contain an uppercase character.")
    parser.add_argument("--type_mapping", type=str, default=settings.WHITELIST_TYPE_MAPPING,
                        help="For pure prior linker: Map predicted entities to types using the given mapping.")
    parser.add_argument("-m", "--multiprocessing", type=int, default=1,
                        help="Number of processes to use. Default is 1.")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    args = parser.parse_args()
    linking_system = LinkingSystem(args.linker_type,
                                   args.linker,
                                   args.link_linker,
                                   args.coreference_linker,
                                   args.kb_name,
                                   args.minimum_score,
                                   args.longest_alias_ner,
                                   args.type_mapping)

    main()
