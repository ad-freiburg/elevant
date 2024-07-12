from flask import Flask, request, Response
import sys
import argparse
from pynif import NIFCollection
from urllib.parse import quote

from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper

sys.path.append(".")

from elevant import settings
from elevant.utils import log
from elevant.linkers.linkers import Linkers, CoreferenceLinkers, PredictionFormats
from elevant.linkers.linking_system import LinkingSystem
from elevant.models.article import Article, article_from_json

app = Flask(__name__)


@app.route('/api/nif', methods=['POST'])
def nif_api():
    nif_body = request.data
    nif_doc = NIFCollection.loads(nif_body)
    for context in nif_doc.contexts:
        article = Article(-1, "", context.mention, [])
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
                if KnowledgeBaseMapper.is_unknown_entity(em.entity_id):
                    entity_uri = 'http://example.org/unknown/some_entity'
                else:
                    if args.wikidata_annotations:
                        entity_uri = 'http://www.wikidata.org/entity/' + em.entity_id
                    else:
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

    linker_group = parser.add_mutually_exclusive_group(required=True)
    linker_group.add_argument("-l", "--linker_name", choices=[li.value for li in Linkers],
                              help="Entity linker name.")
    linker_group.add_argument("-pfile", "--prediction_file",
                              help="Path to predictions file.")

    parser.add_argument("--linker_config",
                        help="Configuration file for the specified linker."
                             "Per default, the system looks for the config file at configs/<linker_name>.config.json")
    parser.add_argument("-pformat", "--prediction_format", choices=[pf.value for pf in PredictionFormats],
                        help="Format of the prediction file.")
    parser.add_argument("-pname", "--prediction_name", default="Unknown Linker",
                        help="Name of the system that produced the predictions.")

    parser.add_argument("-coref", "--coreference_linker", choices=[cl.value for cl in CoreferenceLinkers],
                        help="Coreference linker to apply after entity linkers.")
    parser.add_argument("--only_pronouns", action="store_true",
                        help="Only link coreferences that are pronouns.")
    parser.add_argument("-min", "--minimum_score", type=int, default=0,
                        help="Minimum entity score to include entity in database")
    parser.add_argument("--uppercase", action="store_true",
                        help="Set to remove all predictions on snippets which do not contain an uppercase character.")
    parser.add_argument("--type_mapping", type=str, default=settings.QID_TO_WHITELIST_TYPES_DB,
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

    linking_system = LinkingSystem(args.linker_name,
                                   args.linker_config,
                                   args.prediction_file,
                                   args.prediction_format,
                                   args.prediction_name,
                                   args.coreference_linker,
                                   args.minimum_score,
                                   args.type_mapping)

    if not args.wikidata_annotations and not linking_system.entity_db.is_wikidata_to_wikipedia_mapping_loaded():
        linking_system.entity_db.load_wikidata_to_wikipedia_mapping()

    app.run(host="::", port=args.port, threaded=True)
