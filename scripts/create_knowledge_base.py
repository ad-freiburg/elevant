import argparse
import sys

sys.path.append(".")

from elevant import settings
from elevant.utils import log
from elevant.models.entity_database import EntityDatabase
from elevant.helpers.knowledge_base_creator import KnowledgeBaseCreator


def main(args):
    logger.info("Loading entity database ...")
    entity_db = EntityDatabase()
    entity_db.load_all_entities_in_wikipedia(minimum_sitelink_count=args.min_score)
    entity_db.load_family_name_aliases()
    entity_db.load_alias_to_entities()
    entity_db.load_wikipedia_to_wikidata_db()
    entity_db.load_redirects()
    entity_db.load_link_frequencies()
    entity_db.load_sitelink_counts()

    logger.info("Creating knowledge base...")
    kb = KnowledgeBaseCreator.create_kb(entity_db=entity_db)

    logger.info("Knowledge base contains %d entities." % kb.get_size_entities())
    logger.info("Knowledge base contains %d aliases." % kb.get_size_aliases())

    logger.info("Writing Knowledge base to %s ..." % settings.KB_FILE)
    kb.dump(settings.KB_FILE)

    logger.info("Writing vocabulary to %s ..." % settings.VECTORS_DIRECTORY)
    kb.vocab.to_disk(settings.VOCAB_DIRECTORY)

    logger.info("Wrote knowledge base to %s" % settings.KB_FILE)
    logger.info("Wrote vocab to %s" % settings.VOCAB_DIRECTORY)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("min_score", type=int,
                        help="Minimum score.")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main(parser.parse_args())
