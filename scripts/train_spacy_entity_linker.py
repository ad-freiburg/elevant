import sys
import spacy
from spacy.kb import KnowledgeBase

sys.path.append(".")

from elevant import settings
from elevant.utils import log
from elevant.helpers.entity_database_reader import EntityDatabaseReader
from elevant.helpers.label_generator import LabelGenerator


def train():
    load_path = settings.KB_DIRECTORY + "wikipedia/"
    vocab_path = load_path + "vocab"
    kb_path = load_path

    logger.info("Loading model ...")
    nlp = spacy.load(settings.LARGE_MODEL_NAME)
    nlp.vocab.from_disk(vocab_path)
    # kb = KnowledgeBase(vocab=nlp.vocab, entity_vector_length=300)
    # kb.from_disk(kb_path)
    # entity_linker = nlp.create_pipe("entity_linker", {"incl_prior": args.prior})

    def create_kb(vocab):
        kb = KnowledgeBase(vocab=vocab, entity_vector_length=300)
        kb.from_disk(kb_path)
        logger.info("Knowledge base contains %d entities." % kb.get_size_entities())
        logger.info("Knowledge base contains %d aliases." % kb.get_size_aliases())
        return kb

    # create entity linker with the knowledge base and add it to the pipeline:
    entity_linker = nlp.add_pipe("entity_linker", config={"incl_prior": False}, last=True)
    logger.info("Loading knowledge base ...")
    entity_linker.set_kb(create_kb)
    kb = nlp.get_pipe("entity_linker").kb
    mapping = EntityDatabaseReader.get_wikipedia_to_wikidata_db()
    generator = LabelGenerator(kb, mapping)
    example = next(generator.read_examples())
    entity_linker.initialize(get_examples=lambda: [example])
    print(f"hyperparameters: {entity_linker.cfg}")

    from spacy.util import minibatch

    with nlp.select_pipes(enable=["entity_linker"]):  # train only the entity_linker
        optimizer = nlp.resume_training()
        print(nlp.get_pipe("entity_linker").cfg)
        for itn in range(1):
            batches = minibatch(generator.read_examples(n=100), size=1)
            losses = {}
            for batch in batches:
                nlp.update(
                    batch,
                    drop=0.2,  # prevent overfitting
                    losses=losses,
                    sgd=optimizer,
                )
            if itn % 10 == 0:
                print(itn, "Losses", losses)  # print the training loss
    print(itn, "Losses", losses)
    entity_linker.to_disk(settings.SPACY_MODEL_DIRECTORY + "spacy_batch1_model")


if __name__ == "__main__":
    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    train()
