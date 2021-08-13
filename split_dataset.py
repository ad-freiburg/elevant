import random
import argparse

from src.helpers.wikinews_dump_reader import WikinewsDumpReader
from src.helpers.wikipedia_dump_reader import WikipediaDumpReader
from src import settings


PRINT_EVERY = 100
random.seed(42)


def main(args):
    dev_filename = settings.WIKINEWS_DEVELOPMENT_ARTICLES if args.wikinews else settings.DEVELOPMENT_ARTICLES
    test_filename = settings.WIKINEWS_TEST_ARTICLES if args.wikinews else settings.TEST_ARTICLES
    train_filename = settings.WIKINEWS_TRAINING_ARTICLES if args.wikinews else settings.TRAINING_ARTICLES

    json_iterator = WikinewsDumpReader.json_iterator(yield_none=True) if args.wikinews else \
        WikipediaDumpReader.json_iterator(yield_none=True)

    print("reading articles...")
    articles = []
    for i, article in enumerate(json_iterator):
        if i % PRINT_EVERY == 0 or article is None:
            print("\r%i articles" % i, end='')
        if article is None:
            print()
            break
        articles.append(article)

    print("shuffling articles...")
    random.shuffle(articles)

    print("writing articles...")
    with open(train_filename, "w") as f_train, \
            open(dev_filename, "w") as f_dev, \
            open(test_filename, "w") as f_test:
        n_train = n_dev = n_test = 0
        for i, article in enumerate(articles):
            if i < args.num_dev_test:
                f_dev.write(article)
                n_dev += 1
            elif i < 2 * args.num_dev_test:
                f_test.write(article)
                n_test += 1
            else:
                f_train.write(article)
                n_train += 1
            if (i + 1) % PRINT_EVERY == 0 or i + 1 == len(articles):
                print("\r%i training, %i development, %i test articles" % (n_train, n_dev, n_test), end='')
        print()
    print("Wrote article splits to \n%s\n%s\n%s" % (train_filename, dev_filename, test_filename))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)
    parser.add_argument("-wn", "--wikinews", action="store_true",
                        help="Get dataset split for Wikinews instead of Wikipedia.")
    parser.add_argument("-n", "--num_dev_test", default=10000, type=int,
                        help="Number of articles in the development and test set.")

    main(parser.parse_args())
