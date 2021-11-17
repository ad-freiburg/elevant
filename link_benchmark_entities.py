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
import time
import log
import sys
import os

from src import settings
from src.evaluation.benchmark import Benchmark
from src.linkers.linkers import Linkers, CoreferenceLinkers, LinkLinkers
from src.linkers.linking_system import LinkingSystem
from src.evaluation.examples_generator import get_example_generator


def main(args):
    if args.link_linker:
        if args.benchmark != Benchmark.WIKI_EX.value and args.benchmark != Benchmark.CONLL_PSEUDO_LINKS.value:
            logger.warning("Using a link linker only makes sense over benchmarks that contain hyperlinks.")
    if args.coreference_linker == "wexea" and not args.linker_type == "wexea":
        logger.error("Wexea can only be used as coreference linker in combination with the Wexea linker")
        exit(1)

    linking_system = LinkingSystem(args.linker_type,
                                   args.linker,
                                   args.link_linker,
                                   args.coreference_linker,
                                   args.kb_name,
                                   args.minimum_score,
                                   args.longest_alias_ner,
                                   args.type_mapping)

    example_generator = get_example_generator(args.benchmark)

    out_dir = os.path.dirname(args.output_file)
    if out_dir and not os.path.exists(out_dir):
        logger.info("Creating directory %s" % out_dir)
        os.makedirs(out_dir)

    output_file = open(args.output_file, 'w', encoding='utf8')

    logger.info("Linking entities in %s benchmark ..." % args.benchmark)

    for i, article in enumerate(example_generator.iterate(args.n_articles)):
        article_start_time = time.time()
        evaluation_span = article.evaluation_span if args.evaluation_span else None
        linking_system.link_entities(article, args.uppercase, args.only_pronouns, evaluation_span)
        article.set_evaluation_time(time.time() - article_start_time)
        output_file.write(article.to_json() + '\n')
        print("\r%i articles" % (i + 1), end='')
    print()

    output_file.close()

    logger.info("Wrote %d linked articles to %s" % (i+1, args.output_file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("output_file", type=str, default=None,
                        help="Output file for the evaluation results")
    parser.add_argument("linker_type", choices=[li.value for li in Linkers],
                        help="Entity linker type.")
    parser.add_argument("linker",
                        help="Specify the linker to be used, depending on its type:\n"
                             "BASELINE: Choose baseline from {scores, links, links-all, max-match-ner}.\n"
                             "SPACY: Name of the linker.\n"
                             "EXPLOSION: Full path to the saved model.\n"
                             "AMBIVERSE: Full path to the predictions directory.\n"
                             "IOB: Full path to the prediction file in IOB format (for CoNLL benchmark only).\n")
    parser.add_argument("-b", "--benchmark", choices=[b.value for b in Benchmark], default=Benchmark.WIKI_EX.value,
                        help="Benchmark over which to evaluate the linker.")
    parser.add_argument("-n", "--n_articles", type=int, default=-1,
                        help="Number of articles to evaluate on.")
    parser.add_argument("-kb", "--kb_name", type=str, choices=["wikipedia"], default=None,
                        help="Name of the knowledge base to use with a spacy linker.")
    parser.add_argument("-ll", "--link_linker", choices=[ll.value for ll in LinkLinkers], default=None,
                        help="Link linker to apply before spacy or explosion linker")
    parser.add_argument("-coref", "--coreference_linker",
                        choices=[cl.value for cl in CoreferenceLinkers], default=None,
                        help="Coreference linker to apply after entity linkers.")
    parser.add_argument("--only_pronouns", action="store_true",
                        help="Only link coreferences that are pronouns.")
    parser.add_argument("--evaluation_span", action="store_true",
                        help="If specified, let coreference linker refer only to entities within the evaluation span")
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

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main(parser.parse_args())
