"""
Write articles from (input file | benchmark | Wikipedia dump) to
(file | directory with one article per file).

Per default, articles are written without any annotations.
But you can also choose to annotate (groundtruth labels | linked entities).
The format of entity annotations is [<QID>:<label>|<original>]
"""

import argparse
import os.path
import logging
from typing import Dict

from src.helpers.entity_database_reader import EntityDatabaseReader
from src.helpers.wikipedia_dump_reader import WikipediaDumpReader
from src.helpers.evaluation_examples_generator import OwnBenchmarkExampleReader
from src.models.wikidata_entity import WikidataEntity
from src.models.wikipedia_article import WikipediaArticle, article_from_json

logging.basicConfig(format='%(asctime)s: %(message)s', datefmt="%H:%M:%S", level=logging.INFO)
logger = logging.getLogger(__name__)


def get_entity_text(article: WikipediaArticle, entities: Dict[str, WikidataEntity], links=False, evaluation_span=False):
    """Annotate entity mentions in the article's text."""
    text = article.text
    offset = 0
    if evaluation_span:
        begin, end = article.evaluation_span
        text = text[begin:end]
        offset = begin
    if links:
        return get_linked_entity_text(article, text, offset, entities)
    else:
        return get_labeled_entity_text(article, text, offset, entities)


def get_labeled_entity_text(article, text, offset, entities):
    if article.labels is None:
        return text
    for span, entity_id in sorted(article.labels, reverse=True):
        begin, end = span
        begin -= offset
        end -= offset
        entity_text_snippet = text[begin:end]
        entity_name = entities[entity_id].name if entity_id in entities else ""
        entity_string = "[%s:%s|%s]" % (entity_id, entity_name, entity_text_snippet)
        text = text[:begin] + entity_string + text[end:]
    return text


def get_linked_entity_text(article, text, offset, entities):
    if article.entity_mentions is None:
        return text
    for span, entity_mention in sorted(article.entity_mentions.items(), reverse=True):
        begin, end = span
        begin -= offset
        end -= offset
        entity_text_snippet = text[begin:end]
        # Do not print entities that were recognized but not linked
        if entity_mention.is_linked():
            entity_id = entity_mention.entity_id
            entity_name = entities[entity_id].name if entity_id in entities else ""
            entity_string = "[%s:%s|%s]" % (entity_id, entity_name, entity_text_snippet)
            text = text[:begin] + entity_string + text[end:]
    return text


def input_file_iterator(filename, num_articles):
    for i, line in enumerate(open(filename, 'r', encoding='utf8')):
        if i == num_articles:
            return
        article = article_from_json(line)
        yield article


def main(args):
    if args.output_file:
        output_file = open(args.output_file, 'w', encoding='utf8')
    elif not os.path.isdir(args.output_dir):
        logger.error("%s is not a directory." % args.output_dir)
        exit(1)

    if args.input_benchmark:
        article_text_iterator = OwnBenchmarkExampleReader.iterate(args.num_articles)
    elif args.input_wiki_dump:
        article_text_iterator = WikipediaDumpReader.article_iterator(args.num_articles)
    else:
        article_text_iterator = input_file_iterator(args.input_file, args.num_articles)

    logger.info("Loading entities...")
    entities = EntityDatabaseReader.read_entity_database()

    article_num = 0
    for article in article_text_iterator:
        text = article.text
        if args.evaluation_span:
            begin, end = article.evaluation_span
            text = text[begin:end] + "\n" if not text[begin:end] == text else text

        if args.print_labels or args.print_links:
            evaluation_span = args.evaluation_span
            text = get_entity_text(article, entities, args.print_links, evaluation_span)

        if args.output_dir:
            file_name = "article_%05d" % article_num
            output_file = open(os.path.join(args.output_dir, file_name), 'w', encoding='utf8')

        article_num += 1

        if args.article_header:
            output_file.write("***** %s (%i) *****\n" % (article.title, article.id))
        output_file.write(text + "\n")

        if args.output_dir:
            output_file.close()

    if args.output_file:
        logger.info("Wrote %d articles to file %s" % (article_num, args.output_file))
    else:
        logger.info("Wrote %d articles to directory %s" % (article_num, args.output_dir))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    group_input = parser.add_mutually_exclusive_group(required=True)

    group_input.add_argument("-i", "--input_file", type=str,
                             help="Input file with one article per line in jsonl format.")

    group_input.add_argument("--input_benchmark", default=False, action="store_true",
                             help="Iterate over own benchmark articles.")

    group_input.add_argument("--input_wiki_dump", default=False, action="store_true",
                             help="Iterate over raw Wikipedia dump articles.")

    group_output = parser.add_mutually_exclusive_group(required=True)

    group_output.add_argument("-o", "--output_file", type=str,
                              help="Output file.")

    group_output.add_argument("--output_dir", type=str,
                              help="Each article is written to a separate file article_xxxxx in the output directory.")

    parser.add_argument("-n", "--num_articles", type=int, default=None,
                        help="Maximum number of articles to process.")

    parser.add_argument("--evaluation_span", default=False, action="store_true",
                        help="Write only sentences within the evaluation span (iff input_benchmark is set).")

    parser.add_argument("--article_header", default=False, action="store_true",
                        help="Write header for each article with title and id.")

    group_links = parser.add_mutually_exclusive_group()
    group_links.add_argument("--print_labels", default=False, action="store_true",
                             help="Print groundtruth labels in the format [<QID>:<label>|<original>].")

    group_links.add_argument("--print_links", default=False, action="store_true",
                             help="Print linked entities in the format [<QID>:<label>|<original>].")

    main(parser.parse_args())
