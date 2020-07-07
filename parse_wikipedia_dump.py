import sys

import json

from src.wikipedia_dump_reader import WikipediaDumpReader
from src.markup_processor import MarkupProcessor


DATA_DIR = "/home/hertel/wikipedia/simplewiki/"
DUMP_FILE = DATA_DIR + "simplewiki-20200601-pages-articles-multistream.xml.bz2"
ARTICLES_WITH_LINKS_FILE = DATA_DIR + "articles_with_links.txt"


def print_help():
    print("Usage:\n"
          "  python3 parse_wikipedia_dump.py <dump_file> <output_file>\n"
          "\n"
          "Example:\n"
          "  python3 parse_wikipedia_dump.py %s %s" % (DUMP_FILE, ARTICLES_WITH_LINKS_FILE))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print_help()
        exit(1)
    dump_file = sys.argv[1]
    out_file = sys.argv[2]
    with open(out_file, "w") as f:
        for i, page in enumerate(WikipediaDumpReader.page_iterator(dump_file)):
            article = WikipediaDumpReader.parse_article(page)
            MarkupProcessor.link_entities(article)
            # TODO: this has changed:
            article_dump = json.dumps({"id": article.id,
                                       "title": article.title,
                                       "paragraphs": article.paragraphs,
                                       "links": article.wikipedia_links})
            f.write(article_dump + '\n')
            print("\r%i articles" % (i + 1), end='')
        print()
