import requests
import argparse
from src import settings
from src.helpers.entity_database_reader import EntityDatabaseReader

QUERY = "PREFIX wdt: <http://www.wikidata.org/prop/direct/> " \
        "PREFIX wd: <http://www.wikidata.org/entity/> " \
        "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>" \
        "SELECT DISTINCT ?item ?type WHERE " \
        "{ { ?item wdt:P31 ?type . " \
        "VALUES ?type { %s } } " \
        "UNION " \
        "{ ?item wdt:P31 ?m . ?m wdt:P279+ ?type . " \
        "VALUES ?type { %s } } }"

QUERY_REPAIR_DATA_ERROR = "PREFIX wdt: <http://www.wikidata.org/prop/direct/> " \
        "PREFIX wd: <http://www.wikidata.org/entity/> " \
        "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>" \
        "SELECT DISTINCT ?item ?type WHERE " \
        "{ { { ?item wdt:P31 ?type . " \
        "VALUES ?type { %s } } " \
        "UNION " \
        "{ ?item wdt:P31 ?m . ?m wdt:P279+ ?m2 . ?m2 wdt:P279 ?type . " \
        "VALUES ?type { %s } " \
        "MINUS { VALUES (?m2 ?type) {(wd:Q24229398 wd:Q12737077)} } " \
        "} } UNION { " \
        "?item wdt:P31 ?m . ?m wdt:P279 ?type . " \
        "VALUES ?type { %s } " \
        "MINUS { VALUES (?m ?type) {(wd:Q24229398 wd:Q12737077)} }" \
        "} }"


def get_whitelist():
    whitelist_str = ""
    types = EntityDatabaseReader.read_whitelist_types()
    for typ in types:
        whitelist_str += "wd:" + typ + " "
    return whitelist_str


def main(args):
    whitelist = get_whitelist()
    # query = QUERY % (whitelist, whitelist)
    query = QUERY_REPAIR_DATA_ERROR % (whitelist, whitelist, whitelist)
    url = 'http://galera.informatik.privat:7001/'  # Using the proxy can cause Timeout/MaxRetryError
    data = {"query": query, "action": "tsv_export"}
    r = requests.get(url, params=data)
    with open(args.output_file, "w", encoding="latin1") as file:
        file.write(r.text)
        print("#lines: %d" % (len(r.text.split("\n"))))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("-out", "--output_file", type=str, default=settings.WHITELIST_TYPE_MAPPING,
                        help="Output tsv file with the resulting entity-whitelist-type mapping."
                             "Default: settings.WHITELIST_TYPE_MAPPING")

    main(parser.parse_args())
