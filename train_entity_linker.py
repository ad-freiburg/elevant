import sys
import spacy
from spacy.vocab import Vocab
from spacy.kb import KnowledgeBase
from spacy.language import Language

from src import settings
from src.label_generator import LabelGenerator


def print_help():
    print("Usage:\n"
          "    python3 train_entity_linker.py <batches>")


def save_model(model: Language):
    # save trained model
    model_bytes = model.to_bytes()
    with open(settings.LINKER_DIRECTORY, "wb") as f:
        f.write(model_bytes)
    print("Saved model to", settings.LINKER_DIRECTORY)


PRINT_EVERY = 10
SAVE_EVERY = 10000


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print_help()
        exit(1)

    N_BATCHES = int(sys.argv[1])

    # load the knowledge base:
    vocab = Vocab().from_disk(settings.VOCAB_DIRECTORY)
    kb = KnowledgeBase(vocab=vocab, entity_vector_length=vocab.vectors.shape[1])
    kb.load_bulk(settings.KB_FILE)
    print(kb.get_size_entities(), "entities")
    print(kb.get_size_aliases(), "aliases")

    # make pipeline:
    nlp = spacy.load(settings.LARGE_MODEL_NAME)
    nlp: spacy.language.Language
    entity_linker = nlp.create_pipe("entity_linker",
                                    {"incl_prior": False})
    entity_linker.set_kb(kb)
    nlp.add_pipe(entity_linker, last=True)

    pipe_exceptions = ["entity_linker", "trf_wordpiecer", "trf_tok2vec"]
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe not in pipe_exceptions]

    # initialize model:
    optimizer = nlp.begin_training()

    # initialize label generator:
    generator = LabelGenerator(nlp, kb)

    # iterate over examples:
    print("training...")
    n_batches = 0
    n_examples = 0
    loss_sum = 0
    if N_BATCHES != 0:
        for doc, labels in generator.training_examples():
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
            n_examples += len(batch_docs)
            loss = losses["entity_linker"]
            loss_sum += loss
            loss_mean = loss_sum / n_batches
            if n_batches % PRINT_EVERY == 0:
                print("\r%i batches\t%i examples\tloss: %f\tmean: %f" % (n_batches, n_examples, loss, loss_mean), end='')
            if n_batches == N_BATCHES:
                break
            elif n_batches % SAVE_EVERY == 0:
                print()
                save_model(nlp)
        print()
    save_model(nlp)
