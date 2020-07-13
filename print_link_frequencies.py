import pickle

from src import settings


if __name__ == "__main__":
    with open(settings.LINK_FREEQUENCIES_FILE, "rb") as f:
        links = pickle.load(f)

    for link_text in sorted(links):
        targets = sorted([(target, links[link_text][target]) for target in links[link_text]])
        print(link_text, targets)
