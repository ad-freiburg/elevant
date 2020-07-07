import sys
import spacy

from src.wikipedia_corpus import WikipediaCorpus
from src.link_entity_linker import LinkEntityLinker
from src.trained_entity_linker import TrainedEntityLinker
from src.alias_entity_linker import AliasEntityLinker
from src.coreference_entity_linker import CoreferenceEntityLinker
from src import settings


if __name__ == "__main__":
    in_file = sys.argv[1]
    out_file = sys.argv[2]
    corpus = WikipediaCorpus(settings.DATA_DIRECTORY + in_file)

    model = spacy.load(settings.LARGE_MODEL_NAME)

    link_linker = LinkEntityLinker()
    trained_entity_linker = TrainedEntityLinker(model=model)
    alias_entity_linker = AliasEntityLinker(load_model=False)
    coreference_linker = CoreferenceEntityLinker(model=model)

    with open(settings.DATA_DIRECTORY + out_file, "w") as f:
        for a_i, article in enumerate(corpus.get_articles()):
            for paragraph in article.paragraphs:
                doc = model(paragraph.text)
                link_linker.link_entities(paragraph)
                trained_entity_linker.link_entities(paragraph, doc=doc)
                alias_entity_linker.link_entities(paragraph, doc=doc)
                coreference_linker.link_entities(paragraph, doc=doc)
            f.write(article.to_json() + '\n')
            print("\r%i articles" % (a_i + 1), end='')
        print()
