import argparse
import spacy

from src.models.wikipedia_article import article_from_json


def main(args):
    model = spacy.blank("en")
    model.add_pipe(model.create_pipe("sentencizer"))

    record_id = 0
    wordsfile_name = args.output_prefix + ".wordsfile.tsv"
    docsfile_name = args.output_prefix + ".docsfile.tsv"
    wordsfile = open(wordsfile_name, "w", encoding="utf8")
    docsfile = open(docsfile_name, "w", encoding="utf8")
    with open(args.input_file, "r", encoding="utf8") as input_file:
        for i, json_line in enumerate(input_file):
            if i == args.n_articles:
                break
            article = article_from_json(json_line)
            em_spans = sorted(article.entity_mentions)
            em_idx = 0
            curr_em_span = em_spans[em_idx] if em_idx < len(em_spans) else None
            doc = model(article.text)
            for sent in doc.sents:
                for tok in sent:
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
                if not args.article_records:
                    # Increase the record id after each sentence if records are made up of single sentences
                    record_id += 1

            if args.article_records:
                # Increase record id after each article if records are made up of articles
                record_id += 1

            print("Processed %d articles.\r" % (i+1), end="")

    print("Wrote articles to %s and %s." % (wordsfile_name, docsfile_name))
    
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
    parser.add_argument("--article_records", action="store_true",
                        help="A record is made up of an entire article instead of a single sentence.")

    main(parser.parse_args())
