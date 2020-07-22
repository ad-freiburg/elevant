import sys
import spacy

from src.wikipedia_corpus import WikipediaArticle
from src.wikipedia_dump_reader import WikipediaDumpReader
from src.link_entity_linker import LinkEntityLinker
from src.trained_entity_linker import TrainedEntityLinker
from src.coreference_entity_linker import CoreferenceEntityLinker
from src.alias_entity_linker import AliasEntityLinker, LinkingStrategy
from src.entity_database_new import EntityDatabase
from src import settings
from src.ner_postprocessing import shorten_entities


def print_help():
    print("Usage:\n"
          "    python3 link_wiki_entities.py <in_file> <linker> <name/strategy> <n> <out_file> [-coref] [-raw]\n"
          "\n"
          "Arguments:\n"
          "    <in_file>: Name of the input file with articles in JSON format or raw text.\n"
          "    <linker>: Choose from {spacy, baseline}.\n"
          "    <name/strategy>: Name of the spacy linker, or one of {links, scores} for the baseline.\n"
          "    <n>: Number of articles.\n"
          "    <out_file>: Name of the output file.\n"
          "    -coref: If set, coreference linking is done.\n"
          "    -raw: Set to use an input file with raw text.")


def link_entities(article: WikipediaArticle):
    doc = model(article.text)
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
    linker_name_or_strategy = sys.argv[3]
    n_articles = int(sys.argv[4])
    out_file = sys.argv[5]
    coreference_linking = "-coref" in sys.argv
    raw_input = "-raw" in sys.argv

    model = spacy.load(settings.LARGE_MODEL_NAME)
    model.add_pipe(shorten_entities, name="shorten_ner", after="ner")
    link_linker = LinkEntityLinker()

    if linker_type == "spacy":
        linker = TrainedEntityLinker(name=linker_name_or_strategy, model=model)
    elif linker_type == "baseline":
        strategy_name = linker_name_or_strategy
        if strategy_name not in ("links", "scores", "links-all"):
            raise NotImplementedError("Unknown strategy '%s'." % strategy_name)
        minimum_score = int(sys.argv[5]) if len(sys.argv) > 5 else 0
        entity_db = EntityDatabase()
        if strategy_name in ("links", "links-all"):
            print("load entities...")
            if strategy_name == "links":
                entity_db.load_entities_small(minimum_score)
            else:
                entity_db.load_entities_big()
            print(entity_db.size_entities(), "entities")
            print("load links...")
            entity_db.load_mapping()
            entity_db.load_redirects()
            entity_db.add_link_aliases()
            entity_db.load_link_frequencies()
            print(entity_db.size_aliases(), "aliases")
            strategy = LinkingStrategy.LINK_FREQUENCY
        else:
            print("load entities...")
            entity_db.load_entities_small(minimum_score)
            print(entity_db.size_entities(), "entities")
            print("add synonyms...")
            entity_db.add_synonym_aliases()
            print(entity_db.size_aliases(), "aliases")
            print("add names...")
            entity_db.add_name_aliases()
            print(entity_db.size_aliases(), "aliases")
            strategy = LinkingStrategy.ENTITY_SCORE
        linker = AliasEntityLinker(entity_db, strategy)
    else:
        raise Exception("Unknown linker '%s'." % linker_type)

    if coreference_linking:
        coreference_linker = CoreferenceEntityLinker(model=model)

    with open(settings.DATA_DIRECTORY + out_file, "w") as f:
        for i, line in enumerate(open(settings.SPLIT_ARTICLES_DIR + in_file)):
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
