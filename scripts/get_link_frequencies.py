from itertools import chain
import pickle
import sys

sys.path.append(".")

from elevant import settings
from elevant.utils import log
from elevant.helpers.wikipedia_corpus import WikipediaCorpus
from elevant.models.entity_database import EntityDatabase


def main():
    logger.info("Extracting hyperlink frequencies from Wikipedia training articles.")

    logger.info("Loading entity database...")
    entity_db = EntityDatabase()
    entity_db.load_wikipedia_to_wikidata_db()
    entity_db.load_redirects()

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
            entity_id = entity_db.link2id(target)
            if entity_id is not None:
                if entity_id not in links[link_text]:
                    links[link_text][entity_id] = 1
                else:
                    links[link_text][entity_id] += 1

    with open(settings.LINK_FREEQUENCIES_FILE, "wb") as f:
        pickle.dump(links, f)
    logger.info("Wrote %d hyperlink frequencies to %s." % (len(links), settings.LINK_FREEQUENCIES_FILE))


if __name__ == "__main__":
    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main()
