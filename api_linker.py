from flask import Flask, request, Response
import log
import sys
import argparse
from pynif import NIFCollection
from urllib.parse import quote
from src import settings
from src.linkers.linkers import Linkers, LinkLinkers, CoreferenceLinkers
from src.linkers.linking_system import LinkingSystem
from src.models.wikipedia_article import WikipediaArticle, article_from_json

app = Flask(__name__)


@app.route('/api/nif', methods=['POST'])
def nif_api():
    nif_body = request.data
    nif_doc = NIFCollection.loads(nif_body)
    for context in nif_doc.contexts:
        article = WikipediaArticle(-1, "", context.mention, [])
        if args.input_predictions:
            first_characters = article.text[:100]
            if first_characters in article_dict:
                if article.text != article_dict[first_characters].text:
                    logger.warning("Article text from prediction file (length %d) does not exactly match the article "
                                   "text received by the server (length %d)."
                                   % (len(article_dict[first_characters].text), len(article.text)))
                article = article_dict[first_characters]
            else:
                logger.warning("Article not found in input file: \"%s...\". Return empty predictions."
                               % first_characters)
        else:
            linking_system.link_entities(article, args.uppercase, args.only_pronouns, None)
        if article.entity_mentions:
            for em in sorted(article.entity_mentions.values()):
                entity_uri = 'http://www.wikidata.org/entity/' + em.entity_id
                if not args.wikidata_annotations:
                    wikipedia_title = linking_system.entity_db.id2wikipedia_name(em.entity_id)
                    entity_uri = "https://en.wikipedia.org/wiki/" + quote(wikipedia_title.replace(" ", "_"))
                context.add_phrase(beginIndex=em.span[0], endIndex=em.span[1], taIdentRef=entity_uri)

    resp = Response()
    for header_name, header_value in request.headers.items():
        resp.headers[header_name] = header_value
    resp.data = nif_doc.dumps()
    logger.debug("NIF Response: '%s'" % nif_doc.dumps())

    return resp


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=__doc__)

    parser.add_argument("linker_type", choices=[li.value for li in Linkers],
                        help="Entity linker type.")
    parser.add_argument("linker",
                        help="Specify the linker to be used, depending on its type:\n"
                        "BASELINE: Choose baseline from {scores, links, links-all, max-match-ner}.\n"
                        "SPACY: Name of the linker.\n"
                        "EXPLOSION: Full path to the saved model.\n"
                        "AMBIVERSE: Full path to the predictions directory (for Wikipedia or own benchmark only).\n"
                        "IOB: Full path to the prediction file in IOB format (for CoNLL benchmark only).\n")
    parser.add_argument("-kb", "--kb_name", type=str, choices=["wikipedia"], default=None,
                        help="Name of the knowledge base to use with a spacy linker.")
    parser.add_argument("-ll", "--link_linker", choices=[ll.value for ll in LinkLinkers], default=None,
                        help="Link linker to apply before spacy or explosion linker")
    parser.add_argument("-coref", "--coreference_linker", choices=[cl.value for cl in CoreferenceLinkers], default=None,
                        help="Coreference linker to apply after entity linkers.")
    parser.add_argument("--only_pronouns", action="store_true",
                        help="Only link coreferences that are pronouns.")
    parser.add_argument("-min", "--minimum_score", type=int, default=0,
                        help="Minimum entity score to include entity in database")
    parser.add_argument("--longest_alias_ner", action="store_true",
                        help="For the baselines: use longest matching alias NER instead of SpaCy NER.")
    parser.add_argument("--uppercase", action="store_true",
                        help="Set to remove all predictions on snippets which do not contain an uppercase character.")
    parser.add_argument("--type_mapping", type=str, default=settings.WHITELIST_TYPE_MAPPING,
                        help="For pure prior linker: Map predicted entities to types using the given mapping.")
    parser.add_argument("-wd", "--wikidata_annotations", action="store_true",
                        help="Resulting entity ids will not be mapped to Wikipedia.")
    parser.add_argument("-p", "--port", type=int, default=8080,
                        help="Port for the API.")
    parser.add_argument("-i", "--input_predictions", type=str,
                        help="Read linked articles from file.")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    args = parser.parse_args()

    article_dict = {}
    if args.input_predictions:
        with open(args.input_predictions, "r", encoding="utf8") as file:
            for i, line in enumerate(file):
                article = article_from_json(line)
                first_characters = article.text[:100]
                if first_characters in article_dict:
                    logger.warning("Two articles have the same starting characters: \"%s\"!"
                                   "One article will be overwritten" % first_characters)
                article_dict[first_characters] = article

    linking_system = LinkingSystem(args.linker_type,
                                   args.linker,
                                   args.link_linker,
                                   args.coreference_linker,
                                   args.kb_name,
                                   args.minimum_score,
                                   args.longest_alias_ner,
                                   args.type_mapping)

    if not args.wikidata_annotations and not linking_system.entity_db.is_wikipedia_wikidata_mapping_loaded():
        linking_system.entity_db.load_wikipedia_wikidata_mapping()

    app.run(host="::", port=args.port, threaded=True)
