"""
Write articles from (input file | benchmark | Wikipedia dump) to
(file | directory with one article per file).

Per default, articles are written without any annotations.
But you can also choose to annotate (groundtruth labels | linked entities | hyperlinks).
The format of entity annotations is [<QID>:<label>|<original>]

To write articles in a format that is suitable as Ambiverse (AIDA) input use options
--output_dir <path>

To write articles in a format that is suitable as WEXEA input use options
--output_dir <path> --title_in_filename --print_hyperlinks

To write articles in a format that is suitable as Neural EL (Gupta) input use options
--output_file <path> --one_article_per_line

To write articles in a format that is suitable as Wikifier input use options
--output_dir <path> --ascii
"""

import argparse
import os.path
import sys
import re
from typing import Optional
from enum import Enum

from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper

sys.path.append(".")

from elevant.utils import log
from elevant.evaluation.benchmark import get_available_benchmarks
from elevant.evaluation.benchmark_iterator import get_benchmark_iterator
from elevant.helpers.wikipedia_dump_reader import WikipediaDumpReader
from elevant.models.entity_database import EntityDatabase
from elevant.models.article import Article, article_from_json


class Annotation(Enum):
    LABELS = 0
    LINKS = 1
    HYPERLINKS = 2
    NER = 3


def replace_non_ascii_chars(text: str) -> str:
    return ''.join([char if ord(char) < 128 else '_' for char in text])


def get_entity_text(article: Article,
                    entity_db: EntityDatabase,
                    annotation: Optional[Annotation] = Annotation.LABELS,
                    evaluation_span: Optional[bool] = False):
    """Annotate entity mentions in the article's text."""
    text = article.text
    offset = 0
    if evaluation_span:
        begin, end = article.evaluation_span
        text = text[begin:end]
        offset = begin
    if annotation == Annotation.LABELS:
        return get_labeled_entity_text(article, text, offset, entity_db)
    elif annotation == Annotation.LINKS:
        return get_linked_entity_text(article, text, offset, entity_db)
    elif annotation == Annotation.NER:
        return get_ner_text(article, text, offset), []
    else:
        return get_hyperlink_text(article, text, offset)


def get_labeled_entity_text(article, text, offset, entity_db):
    if article.labels is None:
        return text, []

    label_entities = set()
    for gt_label in sorted(article.labels, reverse=True):
        begin, end = gt_label.span
        begin -= offset
        end -= offset
        entity_text_snippet = text[begin:end]
        entity_name = entity_db.get_entity_name(gt_label.entity_id)
        entity_string = "[%s:%s|%s]" % (gt_label.entity_id, entity_name, entity_text_snippet)
        text = text[:begin] + entity_string + text[end:]
        label_entities.add(gt_label.entity_id)
    return text, list(label_entities)


def get_ner_text(article, text, offset):
    if article.labels is None:
        return text

    for label in sorted(article.labels, reverse=True):
        if label.parent is None and not label.is_optional():
            if KnowledgeBaseMapper.is_unknown_entity(label.entity_id):  # and False:
                continue
            begin, end = label.span
            begin -= offset
            end -= offset
            mention_text_snippet = text[begin:end]
            mention_string = "[[%s]]" % mention_text_snippet
            text = text[:begin] + mention_string + text[end:]
    return text


def get_linked_entity_text(article, text, offset, entity_db):
    if article.entity_mentions is None:
        return text, []

    linked_entities = dict()
    counter = 0
    for span, entity_mention in sorted(article.entity_mentions.items(), reverse=True):
        begin, end = span
        begin -= offset
        end -= offset
        entity_text_snippet = text[begin:end]
        # Do not print entities that were recognized but not linked
        if not KnowledgeBaseMapper.is_unknown_entity(entity_mention.entity_id):
            entity_id = entity_mention.entity_id
            entity_name = entity_db.get_entity_name(entity_id)
            entity_string = "[%s:%s|%s]" % (entity_id, entity_name, entity_text_snippet)
            text = text[:begin] + entity_string + text[end:]
            if entity_id not in linked_entities:
                linked_entities[entity_id] = counter
                counter += 1
    return text, sorted(linked_entities, key=linked_entities.get)  # Sorts by value and returns only keys


def get_hyperlink_text(article, text, offset):
    # Add the bold title span in the first paragraph of an article as hyperlink
    title_spans = []
    for start, end in article.title_synonyms:
        # Do not allow nested hyperlinks and title spans.
        # Only add title span if it is not overlapping with a hyperlink (seems to be WEXEA convention)
        skip = False
        for span, target in sorted(article.hyperlinks):
            link_start = span[0]
            link_end = span[1]
            skip = False
            if link_start <= start < link_end or start <= link_start < end:
                skip = True
                break
            elif link_start > end:
                break
        if not skip:
            title_spans.append(((start, end), article.title))

    if article.hyperlinks + title_spans is None:
        return text, []

    # Annotate text with bold title spans and hyperlinks
    targets = set()
    for span, target in sorted(article.hyperlinks + title_spans, reverse=True):
        begin, end = span
        begin -= offset
        end -= offset
        entity_text_snippet = text[begin:end]
        if entity_text_snippet == target:
            entity_string = "[[%s]]" % target
        else:
            entity_string = "[[%s|%s]]" % (target, entity_text_snippet)
        text = text[:begin] + entity_string + text[end:]
        targets.add(target)
    return text, list(targets)


def input_file_iterator(filename, n_articles):
    for i, line in enumerate(open(filename, 'r', encoding='utf8')):
        if i == n_articles:
            return
        article = article_from_json(line)
        yield article


def main(args):
    if args.output_file:
        output_file = open(args.output_file, 'w', encoding='utf8')
    elif not os.path.isdir(args.output_dir):
        logger.error("%s is not a directory." % args.output_dir)
        exit(1)

    if args.benchmark:
        article_text_iterator = get_benchmark_iterator(args.benchmark).iterate(args.n_articles)
    elif args.input_wiki_dump:
        article_text_iterator = WikipediaDumpReader.article_iterator(args.n_articles)
    else:
        article_text_iterator = input_file_iterator(args.input_file, args.n_articles)

    annotation = None
    if args.print_labels:
        annotation = Annotation.LABELS
    elif args.print_links:
        annotation = Annotation.LINKS
    elif args.print_hyperlinks:
        annotation = Annotation.HYPERLINKS
    elif args.print_ner_groundtruth:
        annotation = Annotation.NER

    entity_db = None
    if annotation is not None:
        logger.info("Loading entities...")
        entity_db = EntityDatabase()
        entity_db.load_entity_names()

    article_num = 0
    for article in article_text_iterator:
        text = article.text
        if args.evaluation_span:
            begin, end = article.evaluation_span
            text = text[begin:end] + "\n" if not text[begin:end] == text else text

        if annotation is not None:
            evaluation_span = args.evaluation_span
            text, entity_list = get_entity_text(article, entity_db, annotation, evaluation_span)
            if args.print_entity_list:
                text += "\nACTUAL ENTITIES\n"
                for ent in entity_list:
                    text += ent + "\n"
                text += "\nOTHER ENTITIES"

        if args.output_dir:
            file_name = "article_%05d" % article_num
            if args.title_in_filename:
                # WEXEA uses the filename as information about the file entity.
                # The prepended article number is needed  for the prediction reader to keep the sorting.
                # It is removed in the adjusted WEXEA code to properly extract the file name.
                file_name += "_" + article.title.replace(" ", '_').replace('/', '_')
            file_name += ".txt"
            output_file = open(os.path.join(args.output_dir, file_name), 'w', encoding='utf8')

        article_num += 1

        separator = "\n"
        if args.one_article_per_line:
            separator = ""
            text = text.replace("\n", " ")
            # Replace weird whitespaces such as no-break space U+00A0
            # TODO: Consider doing this always, not only for one_article_per_line
            text = re.sub(r"\s", " ", text)

        if args.article_header:
            article_title = article.title
            if args.ascii:
                article_title = replace_non_ascii_chars(article.title)
            output_file.write("***** %s (%i) *****%s" % (article_title, article.id, separator))
        if args.ascii:
            text = replace_non_ascii_chars(text)
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

    group_input.add_argument("-b", "--benchmark", choices=get_available_benchmarks(),
                             help="Iterate over benchmark articles of the given benchmark.")

    group_input.add_argument("--input_wiki_dump", default=False, action="store_true",
                             help="Iterate over raw Wikipedia dump articles.")

    group_output = parser.add_mutually_exclusive_group(required=True)

    group_output.add_argument("-o", "--output_file", type=str,
                              help="Output file.")

    group_output.add_argument("--output_dir", type=str,
                              help="Each article is written to a separate file article_xxxxx in the output directory.")

    parser.add_argument("--title_in_filename", action="store_true",
                        help="Sets the title of the article as filename if output_dir is set.")

    parser.add_argument("--one_article_per_line", action="store_true",
                        help="An article is written to a single line.")

    parser.add_argument("-n", "--n_articles", type=int,
                        help="Maximum number of articles to process.")

    parser.add_argument("--evaluation_span", default=False, action="store_true",
                        help="Write only sentences within the evaluation span (iff benchmark is set).")

    parser.add_argument("--article_header", default=False, action="store_true",
                        help="Write header for each article with title and id.")

    group_links = parser.add_mutually_exclusive_group()
    group_links.add_argument("--print_labels", default=False, action="store_true",
                             help="Print groundtruth labels as [<QID>:<label>|<original>].")

    group_links.add_argument("--print_ner_groundtruth", default=False, action="store_true",
                             help="Print NER groundtruth labels as [[<mention>]].")

    group_links.add_argument("--print_links", default=False, action="store_true",
                             help="Print linked entities as [<QID>:<label>|<original>].")

    group_links.add_argument("--print_hyperlinks", default=False, action="store_true",
                             help="Print hyperlinks as [[<target>|<original>]].")

    parser.add_argument("--print_entity_list", action="store_true",
                        help="Print a list of entities at the end of the article")

    parser.add_argument("--ascii", action="store_true",
                        help="Use only ASCII characters in output file(s) and replace errors by '_'.")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main(parser.parse_args())
