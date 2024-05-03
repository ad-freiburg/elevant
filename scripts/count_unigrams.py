import argparse
import sys
import re

sys.path.append(".")

from elevant import settings
from elevant.utils import log
from elevant.helpers.wikipedia_dump_reader import WikipediaDumpReader


def main(args):
    logger.info("Counting unigrams over entire Wikipedia dump ...")
    token_split_re = re.compile(r"\W+")
    frequencies = {}
    for i, article in enumerate(WikipediaDumpReader.article_iterator()):
        tokens = [t for t in token_split_re.split(article.text) if len(t) > 0]
        for t in tokens:
            if t not in frequencies:
                frequencies[t] = 1
            else:
                frequencies[t] += 1
        if (i + 1) % 100 == 0:
            print("\rExtracted %d unigrams from %d articles" % (len(frequencies), i+1), end='')
    print()

    logger.info("Writing unigrams ...")
    with open(args.output_file, "w", encoding="utf8") as output_file:
        for t in sorted(frequencies):
            output_file.write("%s %d\n" % (t, frequencies[t]))
    logger.info("Wrote %d unigram frequencies to %s" % (len(frequencies), args.output_file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=__doc__)

    parser.add_argument("-o", "--output_file", type=str, default=settings.UNIGRAMS_FILE,
                        help="Output file.")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main(parser.parse_args())
