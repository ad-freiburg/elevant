import pickle

from src import settings


if __name__ == "__main__":
    with open(settings.LINK_COUNTS_FILE, "rb") as f:
        link_frequencies = pickle.load(f)

    for link_text in sorted(link_frequencies):
        for entity_id in sorted(link_frequencies[link_text]):
            frequency = link_frequencies[link_text][entity_id]
            print("%s;%s;%i" % (link_text, entity_id, frequency))
