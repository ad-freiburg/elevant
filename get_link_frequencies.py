from itertools import chain
import pickle
import log
import sys

from src.helpers.wikipedia_corpus import WikipediaCorpus
from src import settings


def main():
    logger.info("Extracting link frequencies from Wikipedia training articles.")

    links = {}

    article_iterator = chain(
        WikipediaCorpus.training_articles(),
        iter([None])
    )

    for a_i, article in enumerate(article_iterator):
        if a_i % 100 == 0 or article is None:
            print("\r%i articles, %i unique link texts" % (a_i, len(links)), end='')
        if article is None:
            print()
            break
        for span, target in article.hyperlinks:
            link_text = article.text[span[0]:span[1]]
            if link_text not in links:
                links[link_text] = {}
            if target not in links[link_text]:
                links[link_text][target] = 1
            else:
                links[link_text][target] += 1

    with open(settings.LINK_FREEQUENCIES_FILE, "wb") as f:
        pickle.dump(links, f)
    logger.info("Wrote %d link frequencies to %s." % (len(links), settings.LINK_FREEQUENCIES_FILE))


if __name__ == "__main__":
    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main()
