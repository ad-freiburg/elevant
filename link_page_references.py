import sys

import json

from src.link_entity_linker import LinkEntityLinker
from src.wikipedia_corpus import WikipediaCorpus


def print_help():
    print("Usage:\n"
          "  python3 link_page_references.py <article_file> <mapping_file> <out_file> [v]\n"
          "\n"
          "Examples:\n"
          "  python3 link_page_references.py /home/hertel/wikipedia/wikipedia_2020-06-08/1000_articles_with_links.txt"
          " /home/hertel/wikipedia/wikipedia_2020-06-08/yi-chun/wikidata-wikipedia-mapping.csv"
          " /home/hertel/wikipedia/wikipedia_2020-06-08/1000_articles_with_links_mapped.txt\n"
          "  python3 link_page_references.py /local/data/hertelm/wikipedia_2020-06-08/articles_with_links.txt"
          " /local/data/hertelm/wikipedia_2020-06-08/yi-chun/wikidata-wikipedia-mapping.csv"
          " /local/data/hertelm/wikipedia_2020-06-08/articles_with_links_mapped.txt")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print_help()
        exit(1)
    article_file, mapping_file, out_file = sys.argv[1:4]
    verbose = "v" in sys.argv
    linker = LinkEntityLinker(mapping_file)
    n_mapped = 0
    n_total = 0
    with open(out_file, "w") as out_file:
        for a_i, article in enumerate(WikipediaCorpus(article_file).get_articles()):
            for paragraph in article.paragraphs:
                linker.link_entities(paragraph)
                n_total += len(paragraph.entity_mentions)
                n_mapped += sum(1 for entity in paragraph.entity_mentions if entity.is_linked())
                if verbose:
                    for link, entity in zip(paragraph.wikipedia_links, paragraph.entity_mentions):
                        if entity.entity_id is not None:
                            print("MAPPED %s -> %s" % (link, entity.entity_id))
                        else:
                            print("UNMAPPED", link)
            print("\r%i articles: %.2f%% links mapped (%i/%i)" % (a_i + 1,
                                                                  (n_mapped / n_total * 100) if n_total > 0 else 0,
                                                                  n_mapped,
                                                                  n_total),
                  end='')
            data = article.to_dict()
            out_file.write(json.dumps(data) + "\n")
    print()
