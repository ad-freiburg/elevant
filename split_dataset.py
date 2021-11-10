import json
import pickle
import random
import argparse

from src.helpers.wikipedia_dump_reader import WikipediaDumpReader
from src import settings

PRINT_EVERY = 1000


def main(args):
    random.seed(42)

    dev_ids = []
    dev_ids_set = set()
    test_ids = []
    test_ids_set = set()
    if not args.random_split:
        with open(settings.DEV_AND_TEST_ARTICLE_IDS, "rb") as f:
            ids = pickle.load(f)
        dev_ids = ids["dev"]
        dev_ids_set = set(dev_ids)
        test_ids = ids["test"]
        test_ids_set = set(test_ids)

    print("Reading articles...")
    articles = []
    found_dev_articles = dict()
    found_test_articles = dict()
    train_ids = []
    for i, article in enumerate(WikipediaDumpReader.json_iterator(yield_none=True)):
        if i % PRINT_EVERY == 0 or article is None:
            print("\r%i articles" % i, end='')
        if article is None:
            print()
            break
        json_article = json.loads(article)
        article_id = json_article["id"]
        if not args.random_split:
            if article_id in dev_ids_set:
                found_dev_articles[article_id] = article
            elif article_id in test_ids_set:
                found_test_articles[article_id] = article
            else:
                train_ids.append(article_id)
        articles.append(article)

    print("shuffling articles...")
    random.shuffle(articles)
    random.shuffle(train_ids)

    # Fill up dev and test set with articles if an original dev or test article does not exist anymore
    if not args.random_split and len(found_dev_articles) < args.split_size:
        print("%d original dev article ids missing to reach %d for dev split. Fill up dev set with train articles." %
              (args.split_size - len(found_dev_articles), args.split_size))
        while len(found_dev_articles) < args.split_size:
            article_id = train_ids.pop()
            dev_ids.append(article_id)
            dev_ids_set.add(article_id)
            found_dev_articles[article_id] = None
    if not args.random_split and len(found_test_articles) < args.split_size:
        print("%d original test article ids missing to reach %d for test split. Fill up test set with train articles." %
              (args.split_size - len(found_test_articles), args.split_size))
        while len(found_test_articles) < args.split_size:
            article_id = train_ids.pop()
            test_ids.append(article_id)
            test_ids_set.add(article_id)
            found_test_articles[article_id] = None

    print("Writing articles...")
    if not args.random_split:
        with open(settings.WIKIPEDIA_TRAINING_ARTICLES, "w") as f_train, \
                open(settings.WIKIPEDIA_DEVELOPMENT_ARTICLES, "w") as f_dev, \
                open(settings.WIKIPEDIA_TEST_ARTICLES, "w") as f_test:
            n_train = n_dev = n_test = 0

            # First write dev and test articles in their original order
            print("Write original dev and test articles.")
            for dev_id in dev_ids:
                article = found_dev_articles.get(dev_id)
                if article is not None:
                    f_dev.write(article)
                    n_dev += 1
                    dev_ids_set.remove(dev_id)
            for test_id in test_ids:
                article = found_test_articles.get(test_id)
                if article is not None:
                    f_test.write(article)
                    n_test += 1
                    test_ids_set.remove(test_id)

            print("Write train articles and dev and test articles that were not in the original dev and test set.")
            train_ids = set(train_ids)
            for i, article in enumerate(articles):
                json_article = json.loads(article)
                article_id = json_article["id"]
                if article_id in dev_ids_set:
                    f_dev.write(article)
                    n_dev += 1
                    dev_ids_set.remove(article_id)
                elif article_id in test_ids_set:
                    f_test.write(article)
                    n_test += 1
                    test_ids_set.remove(article_id)
                elif article_id in train_ids:
                    f_train.write(article)
                    n_train += 1
                if (i + 1) % PRINT_EVERY == 0 or i + 1 == len(articles):
                    print("\r%i training, %i development, %i test articles" % (n_train, n_dev, n_test), end='')
    else:
        with open(settings.WIKIPEDIA_TRAINING_ARTICLES, "w") as f_train, \
                open(settings.WIKIPEDIA_DEVELOPMENT_ARTICLES, "w") as f_dev, \
                open(settings.WIKIPEDIA_TEST_ARTICLES, "w") as f_test:
            n_train = n_dev = n_test = 0
            for i, article in enumerate(articles):
                if i < args.split_size:
                    f_dev.write(article)
                    n_dev += 1
                elif i < 2 * args.split_size:
                    f_test.write(article)
                    n_test += 1
                else:
                    f_train.write(article)
                    n_train += 1
                if (i + 1) % PRINT_EVERY == 0 or i + 1 == len(articles):
                    print("\r%i training, %i development, %i test articles" % (n_train, n_dev, n_test), end='')
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("-r", "--random_split", action="store_true",
                        help="Randomly split into train, dev and test set, without using"
                             "ids from original dev and test set.")

    parser.add_argument("-n", "--split_size", type=int, default=10000,
                        help="Number of articles in dev and test set each.")

    main(parser.parse_args())
