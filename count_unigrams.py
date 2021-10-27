import re

from src import settings
from src.helpers.wikipedia_dump_reader import WikipediaDumpReader


if __name__ == "__main__":
    token_split_re = re.compile("\W+")
    frequencies = {}
    for article in WikipediaDumpReader.article_iterator():
        tokens = [t for t in token_split_re.split(article.text) if len(t) > 0]
        for t in tokens:
            if t not in frequencies:
                frequencies[t] = 1
            else:
                frequencies[t] += 1
    with open(settings.UNIGRAMS_FILE, "w", encoding="utf8") as output_file:
        for t in sorted(frequencies):
            output_file.write("%s %d\n" % (t, frequencies[t]))
