import bz2
import pickle
import argparse

from src import settings


TITLE_START = "<title>"
TITLE_END = "</title>"
CATEGORY_PREFIX = "Category:"
WIKIPEDIA_TITLE_PREFIX = "|wikipedia"
SISTERPROJECTS_PREFIX = "|sisterprojects"
PAGE_END = "</page>"


# TODO: Consider also redirects. Right now, e.g. "Orlando" does not exist in the mapping, because the category
#       Orlando is a redirect to "Orlando, Florida"

def main(args):
    category_page = False
    sisterprojects = False
    wikipedia_title = ""
    print("Extracting...")
    mapping = dict()
    for line in bz2.open(args.wikinews_dump_file):
        line = line.decode()
        line = line.strip()
        if line.startswith(TITLE_START):
            line = line[len(TITLE_START):]
            if line.endswith(TITLE_END):
                line = line[:-len(TITLE_END)]
            if line.startswith(CATEGORY_PREFIX):
                title = line[len(CATEGORY_PREFIX):]
                category_page = True
        if category_page:
            if line.startswith(WIKIPEDIA_TITLE_PREFIX):
                wikipedia_title = line.split("=")[1].strip()
            if line.startswith(SISTERPROJECTS_PREFIX):
                # There exist categories like "Fresh Wikinews ideas" which do not have a link to any sisterprojects and
                # do not occur in Wikipedia
                sisterprojects = True
            if line == PAGE_END:
                if sisterprojects:
                    wikipedia_title = title if not wikipedia_title else wikipedia_title
                    mapping[title] = wikipedia_title
                    print("\rExtracted %i mappings from WikiNews categories to Wikipedia titles" % (len(mapping)),
                          end='')

                # Reset values
                category_page = False
                sisterprojects = False
                wikipedia_title = ""

    print()
    print("Extracted mapping for %i category titles." % len(mapping))
    print("Saving...")
    with open(settings.WIKINEWS_CATEGORY_TO_WIKIPEDIA, "wb") as f:
        pickle.dump(mapping, f)
    print("Saved mapping to %s" % settings.WIKINEWS_CATEGORY_TO_WIKIPEDIA)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("wikinews_dump_file", type=str, default=None,
                        help="Wikinews dump file as bz2.")

    main(parser.parse_args())
