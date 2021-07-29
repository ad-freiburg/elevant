import requests
import argparse
from src import settings


QUERY = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>" \
        "PREFIX wdt: <http://www.wikidata.org/prop/direct/>" \
        "PREFIX wd: <http://www.wikidata.org/entity/>" \
        "SELECT DISTINCT ?item ?label WHERE {{{{ " \
        "?item wdt:P279 wd:Q35120 . " \
        "?item @en@rdfs:label ?label " \
        "} UNION { " \
        "?item wdt:P279 ?m . ?m wdt:P279+ wd:Q35120 . " \
        "?item @en@rdfs:label ?label " \
        "}} UNION { " \
        "?item wdt:P31 wd:Q35120 . " \
        "?item @en@rdfs:label ?label " \
        "}} UNION { " \
        "?item wdt:P31 ?m . ?m wdt:P279+ wd:Q35120 . " \
        "?item @en@rdfs:label ?label " \
        '} FILTER REGEX (?item, "Q.+") }'


def main(args):
    url = 'http://galera.informatik.privat:7001/'  # Using the proxy can cause Timeout/MaxRetryError
    data = {"query": QUERY, "action": "tsv_export"}
    r = requests.get(url, params=data)
    with open(args.output_file, "w", encoding="latin1") as file:
        file.write(r.text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("-out", "--output_file", type=str, default=settings.LABEL_MAPPING,
                        help="Output tsv file with the resulting entity-to-label mapping."
                             "Default: settings.LABEL_MAPPING")

    main(parser.parse_args())
