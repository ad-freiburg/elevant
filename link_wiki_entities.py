import sys
import spacy

from src.wikipedia_corpus import WikipediaCorpus
from src.paragraph import Paragraph, paragraph_from_json
from src.link_entity_linker import LinkEntityLinker
from src.trained_entity_linker import TrainedEntityLinker
from src.alias_entity_linker import AliasEntityLinker
from src.coreference_entity_linker import CoreferenceEntityLinker
from src import settings


def print_help():
    print("Usage:\n"
          "    python3 link_wiki_entities.py <in_file> <out_file> [-p] [-a]")


def link_entities(paragraph: Paragraph):
    doc = model(paragraph.text)
    paragraph.remove_entity_mentions()
    link_linker.link_entities(paragraph)
    trained_entity_linker.link_entities(paragraph, doc=doc)
    if link_aliases:
        alias_entity_linker.link_entities(paragraph, doc=doc)
    coreference_linker.link_entities(paragraph, doc=doc)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print_help()
        exit(1)

    in_file = sys.argv[1]
    out_file = sys.argv[2]
    is_paragraph_file = "-p" in sys.argv
    link_aliases = "-a" in sys.argv

    model = spacy.load(settings.LARGE_MODEL_NAME)

    link_linker = LinkEntityLinker()
    trained_entity_linker = TrainedEntityLinker(model=model)
    if link_aliases:
        alias_entity_linker = AliasEntityLinker(load_model=False)
    coreference_linker = CoreferenceEntityLinker(model=model)

    with open(settings.DATA_DIRECTORY + out_file, "w") as f:
        if is_paragraph_file:
            for p_i, line in enumerate(open(settings.DATA_DIRECTORY + in_file)):
                paragraph = paragraph_from_json(line)
                link_entities(paragraph)
                f.write(paragraph.to_json() + '\n')
                print("\r%i paragraphs" % (p_i + 1), end='')
        else:
            corpus = WikipediaCorpus(settings.DATA_DIRECTORY + in_file)
            for a_i, article in enumerate(corpus.get_articles()):
                for paragraph in article.paragraphs:
                    link_entities(paragraph)
                f.write(article.to_json() + '\n')
                print("\r%i articles" % (a_i + 1), end='')
        print()
