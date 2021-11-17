import log
import sys

from src.helpers.wikipedia_dump_reader import WikipediaDumpReader
from src import settings


def main():
    logger.info("Extracting Wikipedia ID to Wikipedia title mapping from entire Wikipedia dump ...")
    wikipedia_id2title = dict()
    for article in WikipediaDumpReader.article_iterator():
        wikipedia_id2title[article.id] = article.title

    logger.info("Writing mapping to file ...")
    with open(settings.WIKIPEDIA_ID_TO_TITLE_FILE, "w", encoding="utf8") as output_file:
        for article_id, article_title in sorted(wikipedia_id2title.items()):
            output_file.write("%s\t%s\n" % (str(article_id), article_title))
    logger.info("Wrote %d Wikipedia ID to Wikipedia title mappings to %s" % (len(wikipedia_id2title),
                                                                             settings.WIKIPEDIA_ID_TO_TITLE_FILE))


if __name__ == "__main__":
    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main()
