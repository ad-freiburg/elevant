import sys
import random

from src import settings
from src.wikipedia_corpus import WikipediaCorpus


if __name__ == "__main__":
    corpus_file = settings.DATA_DIRECTORY + sys.argv[1]
    out_file = settings.DATA_DIRECTORY + sys.argv[2]
    random.seed(3010)

    corpus = WikipediaCorpus(corpus_file)
    paragraphs = []
    print("reading...")
    for a_i, article in enumerate(corpus.get_articles()):
        paragraphs.extend(article.paragraphs)
        if (a_i + 1) % 1000 == 0:
            print("\r%i articles" % (a_i + 1), end='')
    print()

    print("shuffling...")
    random.shuffle(paragraphs)

    print("writing...")
    p_i = 0
    with open(out_file, "w", encoding="utf8") as f:
        for paragraph in paragraphs:
            f.write(paragraph.to_json() + '\n')
            p_i += 1
            if p_i % 1000 == 0:
                print("\r%i paragraphs" % p_i, end='')
    print()
