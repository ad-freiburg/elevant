import sys
import random

from src.wikipedia_dump_reader import WikipediaDumpReader
from src import settings


if __name__ == "__main__":
    N_DEV_TEST = int(sys.argv[1]) if len(sys.argv) > 1 else 10000

    random.seed(42)
    PRINT_EVERY = 100

    print("reading article IDs...")
    ids = []
    for a_i, article in enumerate(WikipediaDumpReader.article_iterator(yield_none=True)):
        if a_i % PRINT_EVERY == 0 or article is None:
            print("\r%i articles" % a_i, end='')
        if article is None:
            print()
            break
        ids.append(article.id)

    print("splitting article IDs...")
    random.shuffle(ids)
    dev_ids = set(ids[:N_DEV_TEST])
    test_ids = set(ids[N_DEV_TEST:(2 * N_DEV_TEST)])

    print("writing articles...")
    with open(settings.TRAINING_ARTICLES, "w") as f_train, \
         open(settings.DEVELOPMENT_ARTICLES, "w") as f_dev, \
         open(settings.TEST_ARTICLES, "w") as f_test:
        n_train = n_dev = n_test = 0
        for a_i, article in enumerate(WikipediaDumpReader.article_iterator(yield_none=True)):
            if a_i % PRINT_EVERY == 0 or article is None:
                print("\r%i training, %i development, %i test articles" % (n_train, n_dev, n_test), end='')
            if article is None:
                print()
                break
            line = article.to_json() + '\n'
            if article.id in dev_ids:
                f_dev.write(line)
                n_dev += 1
            elif article.id in test_ids:
                f_test.write(line)
                n_test += 1
            else:
                f_train.write(line)
                n_train += 1
