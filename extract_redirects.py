import argparse
import log
import bz2
import re
import pickle
import sys
import dbm

from src import settings

TITLE_START = "<title>"
TITLE_END = "</title>"
REDIRECT = "#REDIRECT"
PRINT_EVERY = 100


def main(args):
    dump_file = args.wikipedia_dump

    opening_bracket_pattern = re.compile(r"\[\[")
    closing_bracket_pattern = re.compile(r"]]")

    a_i = 0
    logger.info("Extracting redirects from %s ..." % dump_file)
    with dbm.open(settings.REDIRECTS_DB, "nf") as db:
        for line in bz2.open(dump_file):
            line = line.decode()
            line = line.strip()
            if line.startswith(TITLE_START):
                a_i += 1
                if a_i % PRINT_EVERY == 0:
                    print("\rExtracted %d redirects from %i articles" % (len(db), a_i), end='')
                line = line[len(TITLE_START):]
                if line.endswith(TITLE_END):
                    line = line[:-len(TITLE_END)]
                title = line
            else:
                redirect_index = line.lower().find(REDIRECT.lower())  # ignore case, as some redirects appear as #Redirect
                if redirect_index >= 0:
                    redirect_start = redirect_index + len(REDIRECT)
                    start_match = opening_bracket_pattern.search(line, pos=redirect_start)
                    if start_match:
                        target_start = start_match.end()
                        end_match = closing_bracket_pattern.search(line, pos=target_start)
                        if end_match:
                            target_end = end_match.start()
                            target = line[target_start:target_end]
                            target = target.replace('_', ' ')
                            db[title] = target
        print()
        logger.info("Wrote %d redirects to %s" % (len(db), settings.REDIRECTS_DB))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("wikipedia_dump", type=str,
                        help="Wikipedia dump file.")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main(parser.parse_args())
