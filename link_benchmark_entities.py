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
import os

from src.linkers.linking_system import LinkingSystem
from src.models.entity_database import EntityDatabase
from src.evaluation.examples_generator import ConllExampleReader, OwnBenchmarkExampleReader,\
    WikipediaExampleReader, PseudoLinkConllExampleReader


def initialize_example_generator(benchmark_name):
    if benchmark_name == "conll":
        example_generator = ConllExampleReader()
    elif benchmark_name == "conll-links":
        print("load evaluation entities...")
        entity_db = EntityDatabase()
        entity_db.load_mapping()
        example_generator = PseudoLinkConllExampleReader(entity_db)
    elif benchmark_name == "own":
        example_generator = OwnBenchmarkExampleReader()
    else:
        print("load evaluation entities...")
        entity_db = EntityDatabase()
        entity_db.load_entities_big()
        entity_db.load_mapping()
        entity_db.load_redirects()
        example_generator = WikipediaExampleReader(entity_db)
    return example_generator


def main(args):
    if args.link_linker:
        if args.benchmark != "own" and args.benchmark != "conll-links":
            print("Link linkers can only be evaluated over own benchmark.")
            exit(1)

    linking_system = LinkingSystem(args.linker_type,
                                   args.linker,
                                   args.link_linker,
                                   args.coreference_linker,
                                   args.kb_name,
                                   args.minimum_score,
                                   args.longest_alias_ner)

    example_generator = initialize_example_generator(args.benchmark)

    out_dir = os.path.dirname(args.output_file)
    if out_dir and not os.path.exists(out_dir):
        print("Creating directory %s" % out_dir)
        os.makedirs(out_dir)

    output_file = open(args.output_file, 'w', encoding='utf8')

    for i, article in enumerate(example_generator.iterate(args.n_articles)):
        article_start_time = time.time()
        evaluation_span = article.evaluation_span if args.evaluation_span else None
        linking_system.link_entities(article, args.uppercase, args.only_pronouns, evaluation_span)
        article.set_evaluation_time(time.time() - article_start_time)
        output_file.write(article.to_json() + '\n')
        print("\r%i articles" % (i + 1), end='')
    print()

    output_file.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("output_file", type=str, default=None,
                        help="Output file for the evaluation results")
    parser.add_argument("linker_type", choices=["baseline", "spacy", "explosion", "ambiverse", "iob", "tagme",
                                                "wexea", "neural_el", "trained_model", "none"],
                        help="Entity linker type.")
    parser.add_argument("linker",
                        help="Specify the linker to be used, depending on its type:\n"
                        "BASELINE: Choose baseline from {scores, links, links-all, max-match-ner}.\n"
                        "SPACY: Name of the linker.\n"
                        "EXPLOSION: Full path to the saved model.\n"
                        "AMBIVERSE: Full path to the predictions directory (for Wikipedia or own benchmark only).\n"
                        "IOB: Full path to the prediction file in IOB format (for CoNLL benchmark only).\n")
    parser.add_argument("-b", "--benchmark", choices=["own", "wikipedia", "conll", "conll-links"], default="own",
                        help="Benchmark over which to evaluate the linker.")
    parser.add_argument("-n", "--n_articles", type=int, default=-1,
                        help="Number of articles to evaluate on.")
    parser.add_argument("-kb", "--kb_name", type=str, choices=["wikipedia"], default=None,
                        help="Name of the knowledge base to use with a spacy linker.")
    parser.add_argument("-ll", "--link_linker", choices=["link-linker", "link-text-linker"], default=None,
                        help="Link linker to apply before spacy or explosion linker")
    parser.add_argument("-coref", "--coreference_linker",
                        choices=["neuralcoref", "entity", "stanford", "xrenner", "hobbs"], default=None,
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

    main(parser.parse_args())
