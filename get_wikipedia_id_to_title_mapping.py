from src.helpers.wikipedia_dump_reader import WikipediaDumpReader
from src import settings


if __name__ == "__main__":
    print("Reading Wikipedia dump...")
    wikipedia_id2title = dict()
    for article in WikipediaDumpReader.article_iterator():
        wikipedia_id2title[article.id] = article.title
    print("Writing mapping to file...")
    with open(settings.WIKIPEDIA_ID_TO_TITLE_FILE, "w", encoding="utf8") as output_file:
        for article_id, article_title in sorted(wikipedia_id2title.items()):
            output_file.write("%s\t%s\n" % (str(article_id), article_title))
    print("Wrote %d Wikipedia ID to Wikipedia title mappings to %s" % (len(wikipedia_id2title),
                                                                        settings.WIKIPEDIA_ID_TO_TITLE_FILE))
