import log
import sys

from src import settings
from src.helpers.wikipedia_dump_reader import WikipediaDumpReader


def main():
    logger.info("Extracting Wikipedia abstracts from entire Wikipedia dump ...")
    with open(settings.WIKIPEDIA_ABSTRACTS_FILE, "w", encoding="utf8") as output_file:
        for i, article in enumerate(WikipediaDumpReader.article_iterator()):
            paragraphs = article.text.split("\n\n")
            abstract = ""
            if len(paragraphs) > 1:
                abstract = paragraphs[1]
                if len(abstract) < 100 and "°" in abstract and len(paragraphs) > 2:
                    abstract = paragraphs[2]
            if len(abstract) == 0:
                abstract = article.text[:500]
            abstract = abstract.replace("\n", " ")
            output_file.write("\t".join((
                article.id,
                article.title,
                article.url,
                abstract
            )) + "\n")

        if (i + 1) % 100 == 0:
            print("Processed %d articles.\r" % (i+1), end="")

    logger.info("Wrote %d abstracts to %s" % (i+1, settings.WIKIPEDIA_ABSTRACTS_FILE))


if __name__ == "__main__":
    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main()
