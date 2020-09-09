import argparse
import spacy

from src.entity_coref_linker import EntityCorefLinker
from src.stanford_corenlp_coref_linker import StanfordCoreNLPCorefLinker
from src.wikipedia_corpus import WikipediaArticle
from src.wikipedia_dump_reader import WikipediaDumpReader
from src.link_entity_linker import LinkEntityLinker
from src.link_text_entity_linker import LinkTextEntityLinker
from src.trained_entity_linker import TrainedEntityLinker
from src.neuralcoref_coref_linker import NeuralcorefCorefLinker
from src.alias_entity_linker import AliasEntityLinker, LinkingStrategy
from src.explosion_linker import ExplosionEntityLinker
from src.entity_database import EntityDatabase
from src import settings
from src.ner_postprocessing import NERPostprocessor
from src.xrenner_coref_linker import XrennerCorefLinker


def link_entities(article: WikipediaArticle):
    if model:
        doc = model(article.text)
    else:
        doc = None
    if not args.link_linker:
        article.add_entity_mentions([])
    else:
        link_linker.link_entities(article)
    linker.link_entities(article, doc=doc)
    if coreference_linker:
        coreference_linker.link_entities(article, doc=doc)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str,
                        help="Name of the input file with articles in JSON format or raw text.")
    parser.add_argument("output_file", type=str,
                        help="Name of the output file.")
    parser.add_argument("linker_type", choices=["baseline", "spacy", "explosion"],
                        help="Entity linker type.")
    parser.add_argument("linker",
                        help="Specify the linker to be used, depending on its type:\n"
                        "BASELINE: Choose baseline from {scores, links, links-all, max-match-ner}.\n"
                        "SPACY: Name of the linker.\n"
                        "EXPLOSION: Full path to the saved model.\n")
    parser.add_argument("-raw", "--raw_input", action="store_true",
                        help="Set to use an input file with raw text.")
    parser.add_argument("-n", "--n_articles", type=int, default=-1,
                        help="Number of articles to evaluate on.")
    parser.add_argument("-kb", "--kb_name", type=str, choices=["wikipedia"], default=None,
                        help="Name of the knowledge base to use with a spacy linker.")
    parser.add_argument("-ll", "--link_linker", choices=["link-linker", "link-text-linker"], default=None,
                        help="Link linker to apply before spacy or explosion linker")
    parser.add_argument("-coref", "--coreference_linker", choices=["neuralcoref", "entity", "stanford", "xrenner"],
                        default=None,
                        help="Coreference linker to apply after entity linkers.")
    parser.add_argument("--only_pronouns", action="store_true",
                        help="Only link coreferences that are pronouns.")
    parser.add_argument("-min", "--minimum_score", type=int, default=0,
                        help="Minimum entity score to include entity in database")
    args = parser.parse_args()

    entity_db = EntityDatabase()
    print("load entities...")
    if args.linker_type == "baseline" and args.linker in ("scores", "links"):
        entity_db.load_entities_small()
    else:
        entity_db.load_entities_big()
    print(entity_db.size_entities(), "entities")
    if args.linker_type == "baseline":
        if args.linker in ("links", "links-all"):
            print("load link frequencies...")
            entity_db.load_mapping()
            entity_db.load_redirects()
            entity_db.add_link_aliases()
            entity_db.load_link_frequencies()
        else:
            print("add synonyms...")
            entity_db.add_synonym_aliases()
            print(entity_db.size_aliases(), "aliases")
            print("add names...")
            entity_db.add_name_aliases()
            print(entity_db.size_aliases(), "aliases")

    model = None
    if args.linker_type != "explosion" or args.coreference_linker:
        model = spacy.load(settings.LARGE_MODEL_NAME)
        ner_postprocessor = NERPostprocessor(entity_db)
        model.add_pipe(ner_postprocessor, name="ner_postprocessor", after="ner")

    if args.link_linker == "link-text-linker":
        print("load link text linker entity database...")
        link_linker_entity_db = EntityDatabase()
        link_linker_entity_db.load_entities_big()
        link_linker_entity_db.load_mapping()
        link_linker_entity_db.load_redirects()
        print("add synonyms...")
        link_linker_entity_db.add_synonym_aliases()
        print("add names...")
        link_linker_entity_db.add_name_aliases()
        link_linker = LinkTextEntityLinker(entity_db=link_linker_entity_db)
    elif args.link_linker == "link-linker":
        link_linker = LinkEntityLinker()

    if args.linker_type == "spacy":
        linker_name = args.linker
        linker = TrainedEntityLinker(name=linker_name, entity_db=entity_db, model=model)
    elif args.linker_type == "explosion":
        linker_path = args.linker
        linker = ExplosionEntityLinker(model_path=linker_path, entity_db=entity_db)
    elif args.linker_type == "baseline":
        strategy_name = args.linker
        if strategy_name == "scores":
            strategy = LinkingStrategy.ENTITY_SCORE
        else:
            strategy = LinkingStrategy.LINK_FREQUENCY
        linker = AliasEntityLinker(entity_db, strategy, load_model=False)
    else:
        raise Exception("Unknown linker '%s'." % args.linker_type)

    coreference_linker = None
    if args.coreference_linker == "neuralcoref":
        coreference_linker = NeuralcorefCorefLinker()
    elif args.coreference_linker == "entity":
        coreference_linker = EntityCorefLinker(entity_db=entity_db)
    elif args.coreference_linker == "stanford":
        coreference_linker = StanfordCoreNLPCorefLinker()
    elif args.coreference_linker == "xrenner":
        coreference_linker = XrennerCorefLinker()

    with open(args.output_file, "w") as f:
        for i, line in enumerate(open(args.input_file)):
            if i == args.n_articles:
                break
            if args.raw_input:
                article = WikipediaArticle(id=i, title="", text=line[:-1], links=[])
            else:
                article = WikipediaDumpReader.json2article(line)
            link_entities(article)
            f.write(article.to_json() + '\n')
            print("\r%i articles" % (i + 1), end='')
        print()
