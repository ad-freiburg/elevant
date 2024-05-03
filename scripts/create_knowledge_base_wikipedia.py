import sys
import os

sys.path.append(".")

from elevant import settings
from elevant.utils import log
from elevant.helpers.knowledge_base_creator import KnowledgeBaseCreator


def main():
    kb = KnowledgeBaseCreator.create_kb_wikipedia()
    logger.info("Knowledge base contains %d entities." % kb.get_size_entities())
    logger.info("Knowledge base contains %d aliases." % kb.get_size_aliases())

    if not os.path.exists(settings.KB_DIRECTORY):
        logger.info("Creating directory %s ..." % settings.KB_DIRECTORY)
        os.mkdir(settings.KB_DIRECTORY)

    save_path = settings.KB_DIRECTORY + "wikipedia/"
    if not os.path.exists(save_path):
        logger.info("Creating directory %s ..." % save_path)
        os.mkdir(save_path)

    kb_path = save_path
    logger.info("Writing knowledge base to %s ..." % kb_path)
    kb.to_disk(kb_path)
    vocab_file = save_path + "vocab"
    logger.info("Writing vocab to %s ..." % vocab_file)
    kb.vocab.to_disk(vocab_file)
    logger.info("Wrote knowledge base to %s" % kb_path)
    logger.info("Wrote vocab to %s" % vocab_file)


if __name__ == "__main__":
    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main()
