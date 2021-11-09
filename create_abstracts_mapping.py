import argparse

from src import settings
from src.helpers.wikipedia_corpus import WikipediaCorpus
from src.models.entity_database import EntityDatabase


def main(args):
    print("Loading wikipedia to wikidata mapping...")
    entity_db = EntityDatabase()
    entity_db.load_mapping()
    entity_db.load_redirects()

    mapping_errors = 0
    entity_id_to_abstract = {}
    for i, article in enumerate(WikipediaCorpus.get_articles(args.input_file)):
        abstract_span = article.get_abstract_span()
        abstract = article.text[abstract_span[0]:abstract_span[1]].strip()
        entity_id = entity_db.link2id(article.title)
        if entity_id:
            if entity_id in entity_id_to_abstract:
                # Occurs little more than 100 times with the 20211001 Wikipedia dump
                # and the 20211021 redirects
                print("Article mapped to %s twice: %s and %s"
                      % (entity_id, article.title, entity_id_to_abstract[entity_id][0]))
            entity_id_to_abstract[entity_id] = (article.title, abstract.replace("\n", " "))
        else:
            # 115812 over enwiki-20211001-extracted.sections.jsonl
            mapping_errors += 1
        print("\rRead %d articles" % (i+1), end='')
    print("%d article titles could not be mapped to a QID." % mapping_errors)
    print("Writing sorted mapping to %s" % args.output_file)
    with open(args.output_file, "w", encoding="utf8") as output_file:
        for entity_id, (title, abstract) in sorted(entity_id_to_abstract.items()):
            output_file.write("%s\t%s\t%s\n" % (entity_id, title, abstract))
    print("Wrote %d article abstracts to %s" % (len(entity_id_to_abstract), args.output_file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("input_file", type=str,
                        help="Input file. Extracted Wikipedia dump in jsonl format.")

    parser.add_argument("-o", "--output_file", type=str, default=settings.QID_TO_ABSTRACTS_FILE,
                        help="Output file.")

    main(parser.parse_args())