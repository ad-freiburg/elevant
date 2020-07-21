import pickle

from src import settings


if __name__ == "__main__":
    with open(settings.REDIRECTS_FILE, "rb") as f:
        redirects = pickle.load(f)
    for page in sorted(redirects):
        print(page, "->", redirects[page])
