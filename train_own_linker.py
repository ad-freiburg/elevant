"""
Train a local linker over Wikipedia hyperlink labels.
"""
from typing import Iterator, Tuple, List, Optional
import torch
import spacy
import random
import math
import argparse

from spacy.kb import KnowledgeBase
from src import settings

from src.linkers.link_entity_linker import get_mapping
from src.helpers.label_generator import LabelGenerator
from src.utils.embeddings_extractor import EmbeddingsExtractor
from src.models.neural_net import NeuralNet
from src.utils.offset_converter import OffsetConverter


# Ensure reproducibility
torch.manual_seed(42)
random.seed(246)


def training_batches(x_train: torch.Tensor,
                     y_train: torch.Tensor,
                     batch_size: int) -> Iterator[Tuple[torch.Tensor, torch.Tensor]]:
    """
    Iterator over random batches of size <batch_size> from the training data
    """
    indices = list(range(x_train.size()[0]))
    random.shuffle(indices)
    n_batches = math.ceil(x_train.size()[0] / batch_size)
    for batch_no in range(n_batches):
        begin = batch_no * batch_size
        end = begin + batch_size
        batch_indices = indices[begin:end]
        x = x_train[batch_indices]
        y = y_train[batch_indices]
        yield x, y


class EntityLinkingTrainer:
    def __init__(self, kb_path, vocab_path, prior: Optional[bool] = False, global_model: Optional[bool] = False,
                 save_best: Optional[bool] = False):
        self.prior = prior
        self.model_path = "trained_entity_linking_model.pt"
        self.checkpoint_path = "trained_entity_linking_model.best.pt"
        self.save_best = save_best
        self.lowest_val_loss = None
        self.global_model = global_model

        print("Load spacy model...")
        nlp = spacy.load(settings.LARGE_MODEL_NAME)

        print("Load vocabulary")
        nlp.vocab.from_disk(vocab_path)

        print("Load knowledge base")
        self.kb = KnowledgeBase(vocab=nlp.vocab)
        self.kb.load_bulk(kb_path)
        print(self.kb.get_size_entities(), "entities")
        print(self.kb.get_size_aliases(), "aliases")

        mapping = get_mapping()
        self.generator = LabelGenerator(nlp, self.kb, mapping)

        self.model = None

    def set_model_path(self, model_path: str):
        self.model_path = model_path
        if self.save_best:
            checkpoint_path = model_path[:-len(".pt")] if model_path.endswith(".pt") else model_path
            self.checkpoint_path = checkpoint_path + ".best.pt"

    def initialize_model(self, n_features, hidden_units, dropout):
        self.model = NeuralNet(n_features, hidden_units, 1, dropout)

    def load_model(self, model_path):
        loaded_model = torch.load(model_path)
        if type(loaded_model) is dict:
            self.model = loaded_model['model']
            self.prior = loaded_model.get('prior', False)
        else:
            self.model = loaded_model

    def create_data(self, n_samples: int, test: Optional[bool] = False) -> Tuple[torch.Tensor, torch.Tensor, List[int]]:
        """
        Create X (samples) and y (labels) as torch tensors by iterating over
        Wikipedia articles and using hyperlinks as labels.
        The features are the concatenation of a sentence embedding and a
        candidate entity embedding.
        """
        # Determine input feature size
        if self.global_model:
            # Concatenation of sentence vector, entity vector and mean of already linked entity vectors
            n_features = 3 * self.kb.entity_vector_length
        else:
            # Input is the concatenation of sentence and entity vector
            n_features = 2 * self.kb.entity_vector_length
        if self.prior:
            # One feature for the prior probability of a candidate given the entity mention
            n_features += 1

        x = torch.zeros(n_samples, n_features)
        y = torch.zeros(n_samples, 1)
        samples_counter = 0
        conjugate_indices = []
        for doc, labels in self.generator.read_examples(test=test):
            links = labels['links']
            if self.global_model:
                true_entity_vectors = self.get_true_entity_vectors(links)
            for i, span in enumerate(sorted(links)):
                snippet = doc.text[span[0]:span[1]]
                sentence_span = OffsetConverter.get_sentence(span[0], doc)
                sentence_span = sentence_span.start_char, sentence_span.end_char
                sentence_vector = EmbeddingsExtractor.get_span_embedding(sentence_span, doc)

                if self.global_model:
                    # Get the average of all true entity vectors in the document except for the current one
                    # TODO: Use random vector if there is only one linked entity in the document
                    mean_true_entity_vector = torch.div(torch.sum(true_entity_vectors[:i], 0) +
                                                       torch.sum(true_entity_vectors[i + 1:], 0),
                                                       true_entity_vectors.size()[0])
                    mean_true_entity_vector = mean_true_entity_vector.reshape((1, mean_true_entity_vector.shape[0]))
                for cand, prob in sorted(links[span].items()):
                    if samples_counter >= n_samples:
                        print()
                        return x, y, conjugate_indices

                    entity_vector = torch.Tensor(self.kb.get_vector(cand))
                    entity_vector = entity_vector.reshape((1, entity_vector.shape[0]))
                    input_tensor = torch.cat((sentence_vector, entity_vector), dim=1)
                    if self.global_model:
                        input_tensor = torch.cat((input_tensor, mean_true_entity_vector), dim=1)
                    if self.prior:
                        prior_prob = self.kb.get_prior_prob(cand, snippet)
                        input_tensor = torch.cat((input_tensor, torch.Tensor([[prior_prob]])), dim=1)
                    x[samples_counter] = input_tensor
                    y[samples_counter] = torch.Tensor([prob])
                    samples_counter += 1
                    print(f"\rAdded {samples_counter} samples", end="")
                conjugate_indices.append(samples_counter)

    def get_true_entity_vectors(self, links):
        """
        Retrieve all entity vectors of candidates with probability 1.0 in the
        label generator data for a single document. I.e. the ground truth
        entity vectors
        """
        true_entity_vectors = torch.zeros(len(links), self.kb.entity_vector_length)
        for i, span in enumerate(sorted(links)):
            for cand, prob in sorted(links[span].items()):
                if prob == 1:
                    entity_vector = torch.Tensor(self.kb.get_vector(cand))
                    entity_vector = entity_vector.reshape((1, entity_vector.shape[0]))
                    true_entity_vectors[i] = entity_vector
        return true_entity_vectors

    def train(self,
              x_train: torch.Tensor,
              y_train: torch.Tensor,
              n_epochs: int,
              batch_size: int,
              learning_rate: float,
              x_val: Optional[torch.Tensor] = None,
              y_val: Optional[torch.Tensor] = None):
        """
        Train the neural network.
        """
        self.model.train()
        loss_function = torch.nn.BCELoss()
        optimizer = torch.optim.SGD(self.model.parameters(), lr=learning_rate)
        self.lowest_val_loss = math.inf
        for i in range(n_epochs):
            batches = training_batches(x_train, y_train, batch_size)
            loss = 0
            for j, (X_batch, y_batch) in enumerate(batches):
                y_hat = self.model(X_batch)
                loss = loss_function(y_hat, y_batch)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            print(f"epoch {i + 1}, loss: {float(loss)}")

            # Compute loss over validation set and save best checkpoint
            if x_val is not None and y_val is not None:
                with torch.no_grad():
                    y_hat = self.model(x_val)
                    val_loss = loss_function(y_hat, y_val)
                    print(f"val loss: {float(val_loss)}")
                    if val_loss < self.lowest_val_loss:
                        self.lowest_val_loss = val_loss
                        print(f"New best performing model saved with val loss {float(val_loss)}")
                        if self.save_best:
                            torch.save({
                                'epoch': i,
                                'model': self.model,
                                'optimizer_state_dict': optimizer.state_dict(),
                                'loss': loss,
                                'prior': self.prior,
                                'global_model': self.global_model
                            }, self.checkpoint_path)

    def evaluate(self,
                 x_test: torch.Tensor,
                 y_test: torch.Tensor,
                 conjugate_indices: List[int]):
        """
        Evaluate the trained model.
        """
        self.model.eval()
        with torch.no_grad():
            y_hat = self.model(x_test)
            print(f"Prediction (first 20): {y_hat[:20]}")
            hard_prediction = torch.where(y_hat < 0.5, 0, 1)
            accuracy = torch.where(hard_prediction == y_test, 1, 0).sum() / hard_prediction.size(0)
            print(f"Accuracy: {accuracy.item()}")
            # Compute accuracy for always guessing 0:
            num_zeros = y_test.size(0) - y_test.sum()
            guessing_accuracy = num_zeros / y_test.size(0)
            print(f"Accuracy when always guessing label 0: {guessing_accuracy}")

            # Real world evaluation
            last_idx = 0
            true = 0
            baseline_true = 0
            n_cases = 0
            for idx in conjugate_indices:
                # print(f"Checking from idx {last_idx} to {idx}")
                pred_idx = torch.argmax(y_hat[last_idx:idx])
                true_idx = torch.argmax(y_test[last_idx:idx])
                baseline_idx = torch.argmax(x_test[last_idx:idx, -1])
                if n_cases <= 4:
                    print(f"Predicted index: {pred_idx}. True index: {true_idx}")
                if y_test[last_idx:idx].sum() != 1:
                    print(f"Something went wrong: {y_test[last_idx:idx]}")
                if pred_idx == true_idx:
                    true += 1
                if baseline_idx == true_idx:
                    baseline_true += 1
                n_cases += 1

                last_idx = idx

            accuracy = true / n_cases
            baseline_accuracy = baseline_true / n_cases

            avg_candidates = conjugate_indices[-1] / len(conjugate_indices)
            random_guess_accuracy = 1 / avg_candidates
            print(f"Accuracy: {accuracy}")
            if self.prior:
                print(f"Baseline accuracy (prior prob): {baseline_accuracy}")
            print(f"Guessing accuracy: {random_guess_accuracy}")

    def save_model(self):
        torch.save({'model': self.model, 'prior': self.prior, 'global_model': self.global_model}, self.model_path)
        print(f"Dictionary with trained model saved to {self.model_path}")
        if self.save_best:
            print(f"Best checkpoint saved to {self.checkpoint_path}")


def main(args):
    # Hyperparameters
    n_samples = args.n_samples
    n_test_samples = args.n_test_samples
    n_val_samples = args.n_val_samples
    n_epochs = args.epochs
    batch_size = args.batch_size
    hidden_units = args.hidden_units
    learning_rate = args.learning_rate
    dropout = args.dropout

    if args.kb_name is None:
        vocab_path = settings.VOCAB_DIRECTORY
        kb_path = settings.KB_FILE
    else:
        load_path = settings.KB_DIRECTORY + args.kb_name + "/"
        vocab_path = load_path + "vocab"
        kb_path = load_path + "kb"

    # Build output model path
    if args.output_file:
        model_path = args.output_file
    else:
        lr_str = str(learning_rate).lstrip("0").lstrip(".")
        do_str = str(dropout).lstrip("0").lstrip(".")
        version = "global" if args.global_model else "local"
        version += "_model_"
        version += "vanilla" if not args.prior else "prior"
        model_name = "%s.%i.%iep.%ibs.%ihu.%slr.%sdo" % (version, n_samples, n_epochs, batch_size, hidden_units,
                                                         lr_str, do_str)
        if args.kb_name:
            model_name += ".%s" % args.kb_name
        model_path = settings.LINKER_MODEL_PATH + model_name + ".pt"

    trainer = EntityLinkingTrainer(kb_path, vocab_path, prior=args.prior, global_model=args.global_model,
                                   save_best=args.save_best)

    if not args.load_model:
        trainer.set_model_path(model_path)

        # Build training and validation data
        print("Create training (and validation) data...")
        x_train, y_train, _ = trainer.create_data(n_samples + n_val_samples)
        x_val, y_val = None, None
        if n_val_samples > 0:
            x_train, x_val = x_train[:n_samples], x_train[n_samples:]
            y_train, y_val = y_train[:n_samples], y_train[n_samples:]
        print(f"Training samples size: {x_train.size()}, training labels size: {y_train.size()}")
        print(f"First 20 training labels: {y_train[:20]}")

        # Train the model
        print("Start training...")
        trainer.initialize_model(x_train.size(1), hidden_units, dropout)
        trainer.train(x_train, y_train, n_epochs, batch_size, learning_rate, x_val, y_val)

        # Save the model
        trainer.save_model()
    else:
        trainer.load_model(args.load_model)

    # Build test data
    print("Create test data...")
    x_test, y_test, conjugate_indices_test = trainer.create_data(n_test_samples, test=True)
    print(f"Test samples size: {x_test.size()}, test labels size: {y_test.size()}")
    print(f"First 20 test labels: {y_test[:20]}")

    # Test the model
    trainer.evaluate(x_test, y_test, conjugate_indices_test)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("-o", "--output_file", type=str,
                        help="Output file to write the model to. Should end on '.pt'. Per default this is"
                             "<local/global>_model_<prior/vanilla>.<n_samples>.<epochs>ep.<batch_size>bs.<hidden_units>hu."
                             "<learning_rate>lr.pt")

    parser.add_argument("-n", "--n_samples", type=int, default=100000,
                        help="Number of samples to train on. (Default: 100000)")

    parser.add_argument("-ep", "--epochs", type=int, default=200,
                        help="Number of epochs. (Default: 200)")

    parser.add_argument("-bs", "--batch_size", type=int, default=16,
                        help="Batch size. (Default: 16)")

    parser.add_argument("-hu", "--hidden_units", type=int, default=512,
                        help="Number of hidden units in the network. (Default: 512)")

    parser.add_argument("-lr", "--learning_rate", type=float, default=0.01,
                        help="Learning rate. (Default: 0.01)")

    parser.add_argument("-do", "--dropout", type=float, default=0.2,
                        help="Dropout. (Default: 0.2)")

    parser.add_argument("--n_test_samples", type=int, default=10000,
                        help="Number of samples in the test set. (Default: 10000)")

    parser.add_argument("--n_val_samples", type=int, default=10000,
                        help="Number of samples in the validation set. (Default: 10000)")

    parser.add_argument("--save_best", action="store_true",
                        help="Save a checkpoint of the model that performs best over the validation set.")

    parser.add_argument("--prior", action="store_true",
                        help="Add prior probability to input feature vector.")

    parser.add_argument("--global_model", action="store_true",
                        help="Train a global model by adding mean of already linked entity vectors to input vector.")

    parser.add_argument("-kb", "--kb_name", type=str, default=None, choices=["wikipedia"],
                        help="Name of the knowledgebase.")

    parser.add_argument("--load_model", type=str, default=None,
                        help="Load model from given path instead of training a new model and evaluate over it.")

    main(parser.parse_args())
