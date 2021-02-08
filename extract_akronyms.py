import pickle
import re

from src.helpers.wikipedia_corpus import WikipediaCorpus
from src import settings

_akronym_re = re.compile(r" \(([A-Z]+)\).*")

if __name__ == "__main__":
    PRINT_EVERY = 100

    akronyms = {}

    for a_i, article in enumerate(WikipediaCorpus.training_articles()):
        if a_i % PRINT_EVERY == 0 or article is None:
            print("\r%i articles, %i unique akronyms" % (a_i, len(akronyms)),
                  end='')
        if article is None:
            print()
            break
        for span, target in article.links:
            link_text = article.text[span[0]:span[1]]
            subsequent_text = article.text[span[1]:span[1] + 10]
            akronym_match = re.match(_akronym_re, subsequent_text)
            if akronym_match:
                akronym = akronym_match.group(1)
                # Try to catch something like "Texas (USA)", but don't enforce existence of capital letters due to
                # cases like "German People's Party (DVP)"
                if 2 < len(akronym) <= len(re.findall(r"[\w']+", link_text)):
                    if akronym not in akronyms:
                        akronyms[akronym] = set()
                    akronyms[akronym].add(target)

    with open(settings.AKRONYMS_FILE, "wb") as f:
        pickle.dump(akronyms, f)
    print("Saved akronyms to %s" % settings.AKRONYMS_FILE)
