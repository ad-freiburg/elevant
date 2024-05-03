import pickle
import sys
import re

sys.path.append(".")

from elevant import settings
from elevant.utils import log
from elevant.helpers.wikipedia_corpus import WikipediaCorpus

_akronym_re = re.compile(r" \(([A-Z]+)\).*")


def main():
    logger.info("Extracting akronyms from Wikipedia training articles ...")

    akronyms = {}
    for a_i, article in enumerate(WikipediaCorpus.training_articles()):
        if a_i % 100 == 0 or article is None:
            print("\r%d articles, %d unique akronyms" % (a_i, len(akronyms)), end='')
        if article is None:
            print()
            break
        for span, target in article.hyperlinks:
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

    logger.info("Wrote %d akronyms to %s" % (len(akronyms), settings.AKRONYMS_FILE))


if __name__ == "__main__":
    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main()
