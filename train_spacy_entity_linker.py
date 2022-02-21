import argparse
import log
import sys
import spacy
from spacy.kb import KnowledgeBase
from spacy.language import Language

from src import settings
from src.helpers.entity_database_reader import EntityDatabaseReader
from src.helpers.label_generator import LabelGenerator


def save_model(model: Language, model_name: str):
    path = settings.LINKERS_DIRECTORY + model_name
    model_bytes = model.to_bytes()
    with open(path, "wb") as f:
        f.write(model_bytes)
    logger.info("Saved model to %s" % path)


PRINT_EVERY = 1
SAVE_EVERY = 10000


def main(args):
    # make pipeline:
    if args.kb_name == "0":
        vocab_path = settings.VOCAB_DIRECTORY
        kb_path = settings.KB_FILE
    else:
        load_path = settings.KB_DIRECTORY + args.kb_name + "/"
        vocab_path = load_path + "vocab"
        kb_path = load_path + "kb"

    logger.info("Loading model ...")
    nlp = spacy.load(settings.LARGE_MODEL_NAME)
    nlp.vocab.from_disk(vocab_path)

    # create entity linker with the knowledge base and add it to the pipeline:
    logger.info("Loading knowledge base ...")
    entity_linker = nlp.create_pipe("entity_linker", {"incl_prior": args.prior})
    kb = KnowledgeBase(vocab=nlp.vocab)
    kb.load_bulk(kb_path)
    logger.info("Knowledge base contains %d entities." % kb.get_size_entities())
    logger.info("Knowledge base contains %d aliases." % kb.get_size_aliases())
    entity_linker.set_kb(kb)
    nlp.add_pipe(entity_linker, last=True)

    pipe_exceptions = ["entity_linker", "trf_wordpiecer", "trf_tok2vec"]
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe not in pipe_exceptions]

    # initialize model:
    optimizer = nlp.begin_training()

    # initialize label generator:
    mapping = EntityDatabaseReader.get_wikipedia_to_wikidata_mapping()
    generator = LabelGenerator(nlp, kb, mapping)

    # iterate over training examples (batch size 1):
    logger.info("Training ...")
    n_batches = 0
    n_articles = 0
    n_entities = 0
    loss_sum = 0
    if args.n_batches != 0:
        for doc, labels in generator.read_examples():
            batch_docs = [doc]
            batch_labels = [labels]
            losses = {}
            with nlp.disable_pipes(*other_pipes):
                nlp.update(
                    batch_docs,
                    batch_labels,
                    sgd=optimizer,
                    losses=losses
                )
            n_batches += 1
            n_articles += len(batch_docs)
            n_entities += len(labels["links"])
            loss = losses["entity_linker"]
            loss_sum += loss
            if n_batches % PRINT_EVERY == 0:
                loss_mean = loss_sum / n_batches
                print("\r%i batches\t%i articles\t%i entities\tloss: %f\tmean: %f" %
                      (n_batches, n_articles, n_entities, loss, loss_mean), end='')
            if n_batches == args.n_batches:
                break
            elif n_batches % SAVE_EVERY == 0:
                print()
                save_model(nlp, args.name)
        print()
    save_model(nlp, args.name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("name", type=str,
                        help="Linker name.")
    parser.add_argument("n_batches", type=int,
                        help="Number of batches.")
    parser.add_argument("kb_name", type=str,
                        help="KB name.")
    parser.add_argument("-p", "--prior", type=str, action="store_true",
                        help="Use prior probabilities.")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main(parser.parse_args())
