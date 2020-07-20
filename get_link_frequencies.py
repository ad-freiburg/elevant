import pickle

from src.wikipedia_dump_reader import WikipediaDumpReader
from src import settings


if __name__ == "__main__":
    PRINT_EVERY = 100

    links = {}

    with open(settings.REDIRECTS_FILE, "rb") as f:
        redirects = pickle.load(f)

    article_iterator = WikipediaDumpReader.article_iterator(yield_none=True)

    for a_i, article in enumerate(article_iterator):
        if a_i % PRINT_EVERY == 0 or article is None:
            print("\r%i articles, %i unique link texts" % (a_i, len(links)),
                  end='')
        if article is None:
            print()
            break
        for span, target in article.links:
            link_text = article.text[span[0]:span[1]]
            if target in redirects:
                target = redirects[target]
            if link_text not in links:
                links[link_text] = {}
            if target not in links[link_text]:
                links[link_text][target] = 1
            else:
                links[link_text][target] += 1

    with open(settings.LINK_FREEQUENCIES_FILE, "wb") as f:
        pickle.dump(links, f)
    print("Saved link frequencies to %s." % settings.LINK_FREEQUENCIES_FILE)
