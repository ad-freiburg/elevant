import sys
import spacy

from src.wikipedia_corpus import WikipediaArticle
from src.wikipedia_dump_reader import WikipediaDumpReader
from src.link_entity_linker import LinkEntityLinker
from src.trained_entity_linker import TrainedEntityLinker
from src.coreference_entity_linker import CoreferenceEntityLinker
from src import settings


def print_help():
    print("Usage:\n"
          "    python3 link_wiki_entities.py <in_file> <linker_name> <n> <out_file>")


def link_entities(article: WikipediaArticle):
    doc = model(article.text)
    link_linker.link_entities(article)
    trained_entity_linker.link_entities(article, doc=doc)
    coreference_linker.link_entities(article, doc=doc)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print_help()
        exit(1)

    in_file = sys.argv[1]
    linker_name = sys.argv[2]
    n_articles = int(sys.argv[3])
    out_file = sys.argv[4]

    model = spacy.load(settings.LARGE_MODEL_NAME)

    link_linker = LinkEntityLinker()
    trained_entity_linker = TrainedEntityLinker(name=linker_name, model=model)
    coreference_linker = CoreferenceEntityLinker(model=model)

    with open(settings.DATA_DIRECTORY + out_file, "w") as f:
        for i, line in enumerate(open(settings.SPLIT_ARTICLES_DIR + in_file)):
            if i == n_articles:
                break
            article = WikipediaDumpReader.json2article(line)
            link_entities(article)
            f.write(article.to_json() + '\n')
            print("\r%i articles" % (i + 1), end='')
        print()
