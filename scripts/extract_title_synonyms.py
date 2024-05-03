import pickle
import sys

sys.path.append(".")

from elevant import settings
from elevant.utils import log
from elevant.helpers.wikipedia_corpus import WikipediaCorpus


def main():
    logger.info("Extracting title synonyms from Wikipedia training articles ...")

    title_synonyms = {}

    for a_i, article in enumerate(WikipediaCorpus.training_articles()):
        if a_i % 100 == 0 or article is None:
            print("\r%i articles, %i unique title synonyms" % (a_i, len(title_synonyms)), end='')
        if article is None:
            print()
            break
        if article.title.startswith("List of"):
            # Wikipedia editors are discouraged from using title synonyms for Lists
            continue
        for span in article.title_synonyms:
            title_synonym = article.text[span[0]:span[1]]
            if title_synonym not in title_synonyms:
                title_synonyms[title_synonym] = set()
            title_synonyms[title_synonym].add(article.title)

    with open(settings.TITLE_SYNONYMS_FILE, "wb") as f:
        pickle.dump(title_synonyms, f)
    logger.info("Wrote %d title synonyms to %s" % (len(title_synonyms), settings.TITLE_SYNONYMS_FILE))


if __name__ == "__main__":
    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main()
