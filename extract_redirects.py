import bz2
import re
import pickle
import sys

from src import settings


TITLE_START = "<title>"
TITLE_END = "</title>"
REDIRECT = "#REDIRECT"


if __name__ == "__main__":
    dump_file = sys.argv[1]

    redirect_pattern = re.compile(REDIRECT)
    opening_bracket_pattern = re.compile("\[\[")
    closing_bracket_pattern = re.compile("]]")

    redirects = {}

    print("reading...")
    for line in bz2.open(dump_file):
        line = line.decode()
        line = line.strip()
        if line.startswith(TITLE_START):
            line = line[len(TITLE_START):]
            if line.endswith(TITLE_END):
                line = line[:-len(TITLE_END)]
            title = line
        else:
            redirect_match = redirect_pattern.search(line)
            if redirect_match:
                start_match = opening_bracket_pattern.search(line, pos=redirect_match.end())
                if start_match:
                    target_start = start_match.end()
                    end_match = closing_bracket_pattern.search(line, pos=target_start)
                    if end_match:
                        target_end = end_match.start()
                        target = line[target_start:target_end]
                        print(title, "->", target)
                        redirects[title] = target
    print("read %i redirects" % len(redirects))

    print("saving...")
    with open(settings.REDIRECTS_FILE, "wb") as f:
        pickle.dump(redirects, f)
    print("saved to %s" % settings.REDIRECTS_FILE)
