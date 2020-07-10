import sys

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
    markup_processor = MarkupProcessor()
    with open(out_file, "w") as f:
        for i, page in enumerate(WikipediaDumpReader.page_iterator(dump_file)):
            article = WikipediaDumpReader.parse_article(page)
            markup_processor.filter_markup_and_link_entities(article)
            article_dump = article.to_json()
            f.write(article_dump + '\n')
            print("\r%i paragraphs extracted from %i articles (%i paragraphs removed)" %
                  (markup_processor.n_paragraphs_extracted, (i + 1), markup_processor.n_paragraphs_filtered),
                  end='')
        print()
