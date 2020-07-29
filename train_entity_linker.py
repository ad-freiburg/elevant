import sys
import spacy
from spacy.kb import KnowledgeBase
from spacy.language import Language

from src import settings
from src.link_entity_linker import get_mapping
from src.label_generator import LabelGenerator


def print_help():
    print("Usage:\n"
          "    python3 train_entity_linker.py <name> <batches> <kb_name> [-prior]")


def save_model(model: Language, model_name: str):
    path = settings.LINKERS_DIRECTORY + model_name
    model_bytes = model.to_bytes()
    with open(path, "wb") as f:
        f.write(model_bytes)
    print("Saved model to", path)


PRINT_EVERY = 1
SAVE_EVERY = 10000


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print_help()
        exit(1)

    name = sys.argv[1]
    N_BATCHES = int(sys.argv[2])
    kb_name = sys.argv[3]
    use_prior = "-prior" in sys.argv

    # make pipeline:
    if kb_name == "0":
        vocab_path = settings.VOCAB_DIRECTORY
        kb_path = settings.KB_FILE
    else:
        load_path = settings.KB_DIRECTORY + kb_name + "/"
        vocab_path = load_path + "vocab"
        kb_path = load_path + "kb"

    print("load model...")
    nlp = spacy.load(settings.LARGE_MODEL_NAME)
    nlp.vocab.from_disk(vocab_path)

    # create entity linker with the knowledge base and add it to the pipeline:
    print("load kb...")
    entity_linker = nlp.create_pipe("entity_linker",
                                    {"incl_prior": use_prior})
    kb = KnowledgeBase(vocab=nlp.vocab)
    kb.load_bulk(kb_path)
    print(kb.get_size_entities(), "entities")
    print(kb.get_size_aliases(), "aliases")
    entity_linker.set_kb(kb)
    nlp.add_pipe(entity_linker, last=True)

    pipe_exceptions = ["entity_linker", "trf_wordpiecer", "trf_tok2vec"]
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe not in pipe_exceptions]

    # initialize model:
    optimizer = nlp.begin_training()

    # initialize label generator:
    mapping = get_mapping()
    generator = LabelGenerator(nlp, kb, mapping)

    # iterate over training examples (batch size 1):
    print("training...")
    n_batches = 0
    n_articles = 0
    n_entities = 0
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
            n_articles += len(batch_docs)
            n_entities += len(labels["links"])
            loss = losses["entity_linker"]
            loss_sum += loss
            if n_batches % PRINT_EVERY == 0:
                loss_mean = loss_sum / n_batches
                print("\r%i batches\t%i articles\t%i entities\tloss: %f\tmean: %f" %
                      (n_batches, n_articles, n_entities, loss, loss_mean), end='')
            if n_batches == N_BATCHES:
                break
            elif n_batches % SAVE_EVERY == 0:
                print()
                save_model(nlp, name)
        print()
    save_model(nlp, name)
