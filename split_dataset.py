import sys
import random

from src.wikipedia_dump_reader import WikipediaDumpReader
from src import settings


if __name__ == "__main__":
    N_DEV_TEST = int(sys.argv[1]) if len(sys.argv) > 1 else 10000

    random.seed(42)
    PRINT_EVERY = 100

    print("reading articles...")
    articles = []
    for i, article in enumerate(WikipediaDumpReader.json_iterator(yield_none=True)):
        if i % PRINT_EVERY == 0 or article is None:
            print("\r%i articles" % i, end='')
        if article is None:
            print()
            break
        articles.append(article)

    print("shuffling articles...")
    random.shuffle(articles)

    print("writing articles...")
    with open(settings.TRAINING_ARTICLES, "w") as f_train, \
         open(settings.DEVELOPMENT_ARTICLES, "w") as f_dev, \
         open(settings.TEST_ARTICLES, "w") as f_test:
        n_train = n_dev = n_test = 0
        for i, article in enumerate(articles):
            if i < N_DEV_TEST:
                f_dev.write(article)
                n_dev += 1
            elif i < 2 * N_DEV_TEST:
                f_test.write(article)
                n_test += 1
            else:
                f_train.write(article)
                n_train += 1
            if (i + 1) % PRINT_EVERY == 0 or i + 1 == len(articles):
                print("\r%i training, %i development, %i test articles" % (n_train, n_dev, n_test), end='')
        print()
