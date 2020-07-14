import sys
import spacy

from src.wikipedia_corpus import WikipediaCorpus, WikipediaArticle
from src.link_entity_linker import LinkEntityLinker
from src.trained_entity_linker import TrainedEntityLinker
from src.coreference_entity_linker import CoreferenceEntityLinker
from src import settings


def print_help():
    print("Usage:\n"
          "    python3 link_wiki_entities.py <n> <out_file>")


def link_entities(article: WikipediaArticle):
    doc = model(article.text)
    link_linker.link_entities(article)
    trained_entity_linker.link_entities(article, doc=doc)
    coreference_linker.link_entities(article, doc=doc)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print_help()
        exit(1)

    n_articles = int(sys.argv[1])
    out_file = sys.argv[2]

    model = spacy.load(settings.LARGE_MODEL_NAME)

    link_linker = LinkEntityLinker()
    trained_entity_linker = TrainedEntityLinker(model=model)
    coreference_linker = CoreferenceEntityLinker(model=model)

    with open(settings.DATA_DIRECTORY + out_file, "w") as f:
        for a_i, article in enumerate(WikipediaCorpus.development_articles(n_articles)):
            link_entities(article)
            f.write(article.to_json() + '\n')
            print("\r%i articles" % (a_i + 1), end='')
        print()
