import bz2
import re
import pickle
import sys

from src import settings


TITLE_START = "<title>"
TITLE_END = "</title>"
REDIRECT = "#REDIRECT"
PRINT_EVERY = 100

if __name__ == "__main__":
    dump_file = sys.argv[1]

    opening_bracket_pattern = re.compile(r"\[\[")
    closing_bracket_pattern = re.compile(r"]]")

    redirects = {}
    a_i = 0
    print_next = 100
    print("Extracting...")
    for line in bz2.open(dump_file):
        line = line.decode()
        line = line.strip()
        if line.startswith(TITLE_START):
            a_i += 1
            if a_i % PRINT_EVERY == 0:
                print("\rExtracted %i redirects from %i articles" % (len(redirects), a_i), end='')
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
                        redirects[title] = target
    print("Extracted %i redirects." % len(redirects))
    print("Saving...")
    with open(settings.REDIRECTS_FILE, "wb") as f:
        pickle.dump(redirects, f)
    print("Saved redirects to %s" % settings.REDIRECTS_FILE)
