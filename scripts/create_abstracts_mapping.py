import argparse
import sys

from elevant.utils.knowledge_base_mapper import KnowledgeBaseName, KnowledgeBaseMapper

sys.path.append(".")

from elevant import settings
from elevant.utils import log
from elevant.helpers.wikipedia_corpus import WikipediaCorpus
from elevant.models.entity_database import EntityDatabase


def main(args):
    logger.info("Loading entity database...")
    entity_db = EntityDatabase()
    entity_db.load_wikipedia_to_wikidata_db()
    entity_db.load_redirects()

    mapping_errors = 0
    multi_mapping_errors = 0
    entity_id_to_abstract = {}
    logger.info("Extracting abstracts from %s" % args.input_file)
    for i, article in enumerate(WikipediaCorpus.get_articles(args.input_file)):
        abstract_span = article.get_abstract_span()
        abstract = article.text[abstract_span[0]:abstract_span[1]].strip()
        entity_id = KnowledgeBaseMapper.get_wikidata_qid(article.title, entity_db, kb_name=KnowledgeBaseName.WIKIPEDIA)
        if not KnowledgeBaseMapper.is_unknown_entity(entity_id):
            if entity_id in entity_id_to_abstract:
                # Occurs little more than 100 times with the 20211001 Wikipedia dump
                # and the 20211021 redirects
                logger.debug("Article mapped to %s twice: %s and %s"
                             % (entity_id, article.title, entity_id_to_abstract[entity_id][0]))
                multi_mapping_errors += 1
            entity_id_to_abstract[entity_id] = (article.title, abstract.replace("\n", " "))
        else:
            # 115812 over enwiki-20211001-extracted.sections.jsonl
            mapping_errors += 1
        if (i + 1) % 100 == 0:
            print("\rRead %d articles" % (i+1), end='')
    print()
    logger.info("%d Wikipedia titles could not be mapped to a QID." % mapping_errors)
    logger.info("%d Wikipedia titles were mapped to an already mapped QID." % multi_mapping_errors)

    logger.info("Writing sorted mapping to %s" % args.output_file)
    with open(args.output_file, "w", encoding="utf8") as output_file:
        for entity_id, (title, abstract) in sorted(entity_id_to_abstract.items()):
            output_file.write("%s\t%s\t%s\n" % (entity_id, title, abstract))
    logger.info("Wrote %d article abstracts to %s" % (len(entity_id_to_abstract), args.output_file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=__doc__)

    parser.add_argument("-i", "--input_file", type=str, default=settings.EXTRACTED_WIKIPEDIA_ARTICLES,
                        help="Input file. Extracted Wikipedia dump in jsonl format.")

    parser.add_argument("-o", "--output_file", type=str, default=settings.QID_TO_ABSTRACTS_FILE,
                        help="Output file.")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main(parser.parse_args())
