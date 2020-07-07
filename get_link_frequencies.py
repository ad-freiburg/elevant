import pickle

from src.link_entity_linker import LinkEntityLinker
from src.paragraph_reader import ParagraphReader
from src import settings


PRINT_EVERY = 1000


if __name__ == "__main__":
    linker = LinkEntityLinker()

    link_counts = {}  # text snippet -> {entity id -> count}

    for i, paragraph in enumerate(ParagraphReader.training_paragraphs()):
        for span, target in paragraph.wikipedia_links:
            if linker.contains_name(target):
                begin, end = span
                link_text = paragraph.text[begin:end]
                entity_id = linker.get_entity_id(target)
                if link_text not in link_counts:
                    link_counts[link_text] = {}
                if entity_id not in link_counts[link_text]:
                    link_counts[link_text][entity_id] = 1
                else:
                    link_counts[link_text][entity_id] += 1
        if (i + 1) % PRINT_EVERY == 0:
            print("\r%i paragraphs (%i unique links)" % (i + 1, len(link_counts)), end='')
    print()

    with open(settings.LINK_COUNTS_FILE, "wb") as f:
        pickle.dump(link_counts, f)
    print("Saved counts to %s." % settings.LINK_COUNTS_FILE)
