import argparse
import log
import sys

import spacy
from spacy.tokens.doc import Doc

from src.models.wikipedia_article import article_from_json


def set_custom_sentence_boundaries(doc: Doc):
    """Manually set sentence starts at newline characters if it's not the last
    token in the document and if it's not followed by another newline character.
    """
    for i, token in enumerate(doc):
        if "\n" in token.text and i + 1 < len(doc) and "\n" not in doc[i+1].text:
            doc[i].is_sent_start = True
    return doc


def main(args):
    logger.info("Creating QLever text files for %s" % args.input_file)

    model = spacy.blank("en")
    model.add_pipe(model.create_pipe("sentencizer"))
    model.add_pipe(set_custom_sentence_boundaries)

    record_id = 0
    wordsfile_name = args.output_prefix + ".wordsfile.tsv"
    wordsfile = open(wordsfile_name, "w", encoding="utf8")
    docsfile_name = args.output_prefix + ".docsfile.tsv"
    docsfile = open(docsfile_name, "w", encoding="utf8")
    if args.articlesfile:
        articlesfile_name = args.output_prefix + ".articlesfile.tsv"
        articlesfile = open(articlesfile_name, "w", encoding="utf8")
    with open(args.input_file, "r", encoding="utf8") as input_file:
        for i, json_line in enumerate(input_file):
            if i == args.n_articles:
                break
            article = article_from_json(json_line)

            if args.articlesfile:
                abstract_span = article.get_abstract_span()

            em_spans = sorted(article.entity_mentions)
            em_idx = 0
            curr_em_span = em_spans[em_idx] if em_idx < len(em_spans) else None
            doc = model(article.text)
            for sent in doc.sents:
                for tok in sent:
                    if args.articlesfile:
                        is_abstract = True if abstract_span[0] <= tok.idx < abstract_span[1] else False

                    if tok.is_punct or tok.is_space:
                        # punctuation or whitespaces should not be included in the wordsfile
                        continue

                    wordsfile.write("%s\t%d\t%d\t%d\n" % (tok.text.strip(), 0, record_id, 1))
                    tok_end = tok.idx + len(tok)

                    if curr_em_span and curr_em_span[1] < tok.idx:
                        em_idx += 1
                        curr_em_span = em_spans[em_idx] if em_idx < len(em_spans) else None

                    if curr_em_span and tok.idx >= curr_em_span[0] and tok_end <= curr_em_span[1]:
                        entity_id = article.entity_mentions[curr_em_span].entity_id
                        wordsfile.write("<http://www.wikidata.org/entity/%s>\t%d\t%d\t%d\n" %
                                        (entity_id, 1, record_id, 1))

                docsfile.write("%d\t%s\n" % (record_id, sent.text.strip("\n").replace("\n", " ")))
                if args.articlesfile:
                    articlesfile.write("%d\t%d\t%s\t%s\n" % (record_id, int(is_abstract), article.title, article.url))
                if not args.article_records:
                    # Increase the record id after each sentence if records are made up of single sentences
                    record_id += 1

            if args.article_records:
                # Increase record id after each article if records are made up of articles
                record_id += 1

            if (i + 1) % 100 == 0:
                print("Processed %d articles.\r" % (i+1), end="")

    print()
    logger.info("Wrote %d articles to %s and %s ." % (i+1, wordsfile_name, docsfile_name))
    if args.articlesfile:
        logger.info("Wrote record id to Wikipedia mapping to %s" % articlesfile_name)
    
    wordsfile.close()
    docsfile.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("input_file", type=str,
                        help="Input file. Linked articles in jsonl format.")
    parser.add_argument("output_prefix", type=str,
                        help="Output files prefix.")
    parser.add_argument("-n", "--n_articles", type=int, default=None,
                        help="Number of articles to write to the output files.")
    parser.add_argument("--articlesfile", action="store_true",
                        help="Create an articlesfile with a mapping from record id to Wikipedia title and url.")
    parser.add_argument("--article_records", action="store_true",
                        help="A record is made up of an entire article instead of a single sentence.")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main(parser.parse_args())
