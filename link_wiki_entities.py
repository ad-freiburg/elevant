import sys
import spacy

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


def print_help():
    print("Usage:\n"
          "    python3 link_wiki_entities.py <in_file> <linker_type> <linker> <n> <out_file>"
          " [-coref] [-raw] [-no_links]\n"
          "\n"
          "Arguments:\n"
          "    <in_file>: Name of the input file with articles in JSON format or raw text.\n"
          "    <linker_type>: Choose from {spacy, explosion, baseline}.\n"
          "    <linker>: Name of the spacy linker, or one of {links, links-all, scores} for the baseline,"
          " or the path to the explosion linker.\n"
          "    <n>: Number of articles.\n"
          "    <out_file>: Name of the output file.\n"
          "    -coref: If set, coreference linking is done.\n"
          "    -raw: Set to use an input file with raw text.\n"
          "    -no_links: Do not use page references to link entities.\n"
          "    -link_text_linker: Use link text linker before applying selected linker.")


def link_entities(article: WikipediaArticle):
    if model:
        doc = model(article.text)
    else:
        doc = None
    if no_links:
        article.add_entity_mentions([])
    else:
        link_linker.link_entities(article)
    linker.link_entities(article, doc=doc)
    if coreference_linking:
        coreference_linker.link_entities(article, doc=doc)


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print_help()
        exit(1)

    in_file = sys.argv[1]
    linker_type = sys.argv[2]
    n_articles = int(sys.argv[4])
    out_file = sys.argv[5]
    coreference_linking = "-coref" in sys.argv
    raw_input = "-raw" in sys.argv
    no_links = "-no_links" in sys.argv
    link_text_linker = "-link_text_linker" in sys.argv

    entity_db = EntityDatabase()
    print("load entities...")
    if linker_type == "baseline" and sys.argv[3] in ("scores", "links"):
        entity_db.load_entities_small()
    else:
        entity_db.load_entities_big()
    print(entity_db.size_entities(), "entities")
    if linker_type == "baseline" or link_text_linker:
        if sys.argv[3] in ("links", "links-all"):
            print("load link frequencies...")
            entity_db.load_mapping()
            entity_db.load_redirects()
            entity_db.add_link_aliases()
            entity_db.load_link_frequencies()
        elif link_text_linker:
            print("add synonyms...")
            entity_db.add_synonym_aliases()
            print(entity_db.size_aliases(), "aliases")
            print("add names...")
            entity_db.add_name_aliases()
            print(entity_db.size_aliases(), "aliases")
            print("add redirects...")
            entity_db.load_redirects()
            print(len(entity_db.redirects), "redirects")
        else:
            print("add synonyms...")
            entity_db.add_synonym_aliases()
            print(entity_db.size_aliases(), "aliases")
            print("add names...")
            entity_db.add_name_aliases()
            print(entity_db.size_aliases(), "aliases")

    model = None
    if linker_type != "explosion" or coreference_linking:
        model = spacy.load(settings.LARGE_MODEL_NAME)
        ner_postprocessor = NERPostprocessor(entity_db)
        model.add_pipe(ner_postprocessor, name="ner_postprocessor", after="ner")

    if not no_links:
        link_linker = LinkTextEntityLinker(entity_db=entity_db) if link_text_linker else LinkEntityLinker()

    if linker_type == "spacy":
        linker_name = sys.argv[3]
        linker = TrainedEntityLinker(name=linker_name, entity_db=entity_db, model=model)
    elif linker_type == "explosion":
        linker_path = sys.argv[3]
        linker = ExplosionEntityLinker(model_path=linker_path, entity_db=entity_db)
    elif linker_type == "baseline":
        strategy_name = sys.argv[3]
        if strategy_name not in ("links", "scores", "links-all"):
            raise NotImplementedError("Unknown strategy '%s'." % strategy_name)
        if strategy_name == "scores":
            strategy = LinkingStrategy.ENTITY_SCORE
        else:
            strategy = LinkingStrategy.LINK_FREQUENCY
        linker = AliasEntityLinker(entity_db, strategy, load_model=False)
    else:
        raise Exception("Unknown linker '%s'." % linker_type)

    if coreference_linking:
        coreference_linker = NeuralcorefCorefLinker(model=model)

    with open(out_file, "w") as f:
        for i, line in enumerate(open(in_file)):
            if i == n_articles:
                break
            if raw_input:
                article = WikipediaArticle(id=i, title="", text=line[:-1], links=[])
            else:
                article = WikipediaDumpReader.json2article(line)
            link_entities(article)
            f.write(article.to_json() + '\n')
            print("\r%i articles" % (i + 1), end='')
        print()
