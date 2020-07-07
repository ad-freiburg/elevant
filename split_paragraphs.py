import sys

from src import settings


if __name__ == "__main__":
    paragraph_file = settings.DATA_DIRECTORY + sys.argv[1]

    print("reading...")
    with open(paragraph_file) as f:
        paragraphs = f.readlines()

    n_paragraphs = len(paragraphs)
    print("%i paragraphs" % n_paragraphs)

    n_dev = int(0.1 * n_paragraphs)

    print("writing development...")
    with open(settings.DATA_DIRECTORY + "development.txt", "w") as f_dev:
        for paragraph in paragraphs[:n_dev]:
            f_dev.write(paragraph)

    print("writing test...")
    with open(settings.DATA_DIRECTORY + "test.txt", "w") as f_test:
        for paragraph in paragraphs[n_dev:(2 * n_dev)]:
            f_test.write(paragraph)

    print("writing training...")
    with open(settings.DATA_DIRECTORY + "training.txt", "w") as f_train:
        for paragraph in paragraphs[(2 * n_dev):]:
            f_train.write(paragraph)
