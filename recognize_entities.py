import sys
import time
import json

from src.wikipedia_corpus import WikipediaCorpus
from src.spacy_named_entity_recognizer import SpacyNamedEntityRecognizer


def print_help():
    print("Usage:\n"
          "    python3 recognize_entities.py <corpus_file> <out_file> <n_articles>\n"
          "\n"
          "Examples:\n"
          "    python3 recognize_entities.py"
          " ~/wikipedia/wikipedia_2020-06-08/1000_articles_with_links_mapped.txt"
          " ~/wikipedia/wikipedia_2020-06-08/1000_articles_with_links_mapped+NERed.txt -1\n"
          "    python3 recognize_entities.py"
          " /local/data/hertelm/wikipedia_2020-06-08/articles_with_links_mapped.txt"
          " /local/data/hertelm/wikipedia_2020-06-08/articles_with_links_mapped+NERed.txt 100000")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print_help()
        exit(1)

    CORPUS_FILE = sys.argv[1]
    OUT_FILE = sys.argv[2]
    N_ARTICLES = int(sys.argv[3])

    corpus = WikipediaCorpus(CORPUS_FILE)
    ner = SpacyNamedEntityRecognizer()

    start_time = time.time()
    n_new_entities = 0

    with open(OUT_FILE, "w", encoding="utf8") as out_file:
        for a_i, article in enumerate(corpus.get_articles()):
            if a_i == N_ARTICLES:
                break
            for paragraph in article.paragraphs:
                old_entities = len(paragraph.entity_mentions)
                ner.recognize(paragraph)
                n_new_entities += len(paragraph.entity_mentions) - old_entities
            print("\r%i articles: %i new entities" % (a_i + 1, n_new_entities), end='')
            out_file.write(json.dumps(article.to_dict()) + '\n')
        print()
    print("%f seconds" % (time.time() - start_time))
