import sys
import json

from src.wikipedia_dump_reader import WikipediaDumpReader


if __name__ == "__main__":
    article_titles = set(sys.argv[1:])
    n_found = 0

    for json_dump in WikipediaDumpReader.json_iterator():
        data = json.loads(json_dump)
        if data["title"] in article_titles:
            print(json_dump, end='')
            n_found += 1
            if n_found == len(article_urls):
                break
