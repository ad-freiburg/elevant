import argparse

from src.linkers.linking_system import LinkingSystem
from src.models.wikipedia_article import WikipediaArticle
from src.helpers.wikipedia_dump_reader import WikipediaDumpReader


def main(args):
    linking_system = LinkingSystem(args.linker_type,
                                   args.linker,
                                   args.link_linker,
                                   args.coreference_linker,
                                   args.kb_name,
                                   args.minimum_score,
                                   args.longest_alias_ner)

    input_file = open(args.input_file, 'r', encoding='utf8')
    output_file = open(args.output_file, 'w', encoding='utf8')

    for i, line in enumerate(input_file):
        if i == args.n_articles:
            break
        if args.raw_input:
            article = WikipediaArticle(id=i, title="", text=line[:-1], links=[])
        else:
            article = WikipediaDumpReader.json2article(line)
        linking_system.link_entities(article, args.uppercase, args.only_pronouns)
        output_file.write(article.to_json() + "\n")
        print("\r%i articles" % (i + 1), end='')
    print()

    input_file.close()
    output_file.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("input_file", type=str, default=None,
                        help="Input file with articles in JSON format or raw text.")
    parser.add_argument("output_file", type=str, default=None,
                        help="Output file.")
    parser.add_argument("linker_type", choices=["baseline", "spacy", "explosion", "ambiverse", "iob", "tagme", "none"],
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
    parser.add_argument("-ll", "--link_linker", choices=["link-linker", "link-text-linker"], default=None,
                        help="Link linker to apply before spacy or explosion linker")
    parser.add_argument("-coref", "--coreference_linker",
                        choices=["neuralcoref", "entity", "stanford", "xrenner", "hobbs"], default=None,
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

    main(parser.parse_args())