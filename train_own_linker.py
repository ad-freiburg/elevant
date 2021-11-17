"""
Train a local linker over Wikipedia hyperlink labels.
"""
from typing import Iterator, Tuple, List, Optional
import torch
import spacy
import random
import math
import argparse
import gensim
import log
import sys

from spacy.kb import KnowledgeBase

from src.helpers.entity_database_reader import EntityDatabaseReader
from src.helpers.label_generator import LabelGenerator
from src.utils.embeddings_extractor import EmbeddingsExtractor
from src.models.neural_net import NeuralNet
from src import settings


# Ensure reproducibility
torch.manual_seed(42)
random.seed(246)


def training_batches(x_train: torch.Tensor,
                     y_train: torch.Tensor,
                     batch_size: int) -> Iterator[Tuple[torch.Tensor, torch.Tensor]]:
    """
    Iterator over random batches of size <batch_size> from the training data
    """
    indices = list(range(x_train.shape[0]))
    random.shuffle(indices)
    n_batches = math.ceil(x_train.shape[0] / batch_size)
    for batch_no in range(n_batches):
        begin = batch_no * batch_size
        end = begin + batch_size
        batch_indices = indices[begin:end]
        x = x_train[batch_indices]
        y = y_train[batch_indices]
        yield x, y


class EntityLinkingTrainer:
    def __init__(self,
                 kb_path: str,
                 vocab_path: str,
                 prior: Optional[bool] = False,
                 global_model: Optional[bool] = False,
                 rdf2vec: Optional[bool] = False,
                 save_best: Optional[bool] = False):
        self.prior = prior
        self.model_path = "trained_entity_linking_model.pt"
        self.checkpoint_path = "trained_entity_linking_model.best.pt"
        self.save_best = save_best
        self.lowest_val_loss = None
        self.global_model = global_model

        logger.info("Loading spacy model...")
        nlp = spacy.load(settings.LARGE_MODEL_NAME)

        logger.info("Loading vocabulary...")
        nlp.vocab.from_disk(vocab_path)

        logger.info("Loading knowledge base...")
        self.kb = KnowledgeBase(vocab=nlp.vocab)
        self.kb.load_bulk(kb_path)
        logger.info("Knowledge base contains %d entities." % self.kb.get_size_entities())
        logger.info("Knowledge base contains %d aliases." % self.kb.get_size_aliases())

        self.rdf2vec = rdf2vec
        rdf2vec_model = None
        if rdf2vec:
            logger.info("Loading rdf2vec model...")
            rdf2vec_model = gensim.models.Word2Vec.load(settings.RDF2VEC_MODEL_PATH, mmap='r')

        self.entity_vector_length = rdf2vec_model.wv.vector_size if self.rdf2vec else self.kb.entity_vector_length
        self.embedding_extractor = EmbeddingsExtractor(self.entity_vector_length, self.kb, rdf2vec_model)

        logger.info("Loading Wikipedia - Wikidata mapping...")
        mapping = EntityDatabaseReader.get_wikipedia_to_wikidata_mapping()
        self.generator = LabelGenerator(nlp, self.kb, mapping)

        self.model = None

    def set_model_path(self, model_path: str):
        self.model_path = model_path
        if self.save_best:
            checkpoint_path = model_path[:-len(".pt")] if model_path.endswith(".pt") else model_path
            self.checkpoint_path = checkpoint_path + ".best.pt"

    def initialize_model(self, n_features, hidden_units, dropout):
        self.model = NeuralNet(n_features, hidden_units, 1, dropout)

    def create_data(self, n_samples: int, test: Optional[bool] = False) -> Tuple[torch.Tensor, torch.Tensor, List[int]]:
        """
        Create X (samples) and y (labels) as torch tensors by iterating over
        Wikipedia articles and using hyperlinks as labels.
        The features are the concatenation of vectors depending on the user
        settings.
        """
        # Create empty data matrices
        n_features = self.determine_n_features(300)  # Spacy word vector size. This is fix for now.
        x = torch.zeros(n_samples, n_features)
        y = torch.zeros(n_samples, 1)

        samples_counter = 0
        conjugate_indices = []

        for doc, labels in self.generator.read_examples(test=test):
            links = labels['links']

            if self.global_model:
                true_entity_ids = self.get_true_entity_ids(links)

            for i, span in enumerate(sorted(links)):
                # Get the sentence vector
                sentence_vector = self.embedding_extractor.get_sentence_vector(span, doc)

                if self.global_model:
                    curr_true_entity_ids = true_entity_ids[:i] + true_entity_ids[i+1:]
                    global_entity_vector = self.embedding_extractor.get_global_entity_vector(curr_true_entity_ids)

                snippet = doc.text[span[0]:span[1]]
                for cand, prob in sorted(links[span].items()):
                    # Stop if the required number of samples was reached.
                    if samples_counter >= n_samples:
                        print()
                        return x, y, conjugate_indices

                    # Get the entity vector
                    entity_vector = self.embedding_extractor.get_entity_vector(cand)

                    # Combine vectors into single input vector
                    input_tensor = torch.cat((sentence_vector, entity_vector), dim=1)
                    if self.global_model:
                        input_tensor = torch.cat((input_tensor, global_entity_vector), dim=1)
                    if self.prior:
                        prior_prob = self.kb.get_prior_prob(cand, snippet)
                        input_tensor = torch.cat((input_tensor, torch.Tensor([[prior_prob]])), dim=1)

                    # Update X and y matrices
                    x[samples_counter] = input_tensor
                    y[samples_counter] = torch.Tensor([prob])

                    samples_counter += 1
                    print(f"\rAdded {samples_counter} samples", end="")

                conjugate_indices.append(samples_counter)

    def determine_n_features(self, token_vector_length: int) -> int:
        """
        Determine the number of features of the input vector.
        """
        if self.global_model:
            # Vector of candidate entity, mean vector of already linked entities, sentence vector
            n_features = self.entity_vector_length * 2 + token_vector_length
        else:
            # Vector of candidate entity, sentence vector
            n_features = self.entity_vector_length + token_vector_length

        if self.prior:
            n_features += 1
        return n_features

    def get_true_entity_ids(self, links) -> List[str]:
        """
        Retrieve all entity ids of candidates with probability 1.0 in the label
        generator data for a single document. I.e. the ground truth entity ids.
        """
        true_entity_ids = []
        for i, span in enumerate(sorted(links)):
            for cand, prob in sorted(links[span].items()):
                if prob == 1:
                    true_entity_ids.append(cand)
        return true_entity_ids

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
                                'global_model': self.global_model,
                                'rdf2vec': self.rdf2vec
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
            accuracy = torch.where(hard_prediction == y_test, 1, 0).sum() / hard_prediction.shape[0]
            print(f"Accuracy: {accuracy.item()}")
            # Compute accuracy for always guessing 0:
            num_zeros = y_test.shape[0] - y_test.sum()
            guessing_accuracy = num_zeros / y_test.shape[0]
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
        """
        Save the model and its settings in a dictionary.
        """
        torch.save({'model': self.model, 'prior': self.prior, 'global_model': self.global_model,
                    'rdf2vec': self.rdf2vec}, self.model_path)
        logger.info(f"Dictionary with trained model saved to {self.model_path}")
        if self.save_best:
            logger.info(f"Best checkpoint saved to {self.checkpoint_path}")

    @staticmethod
    def load_model(model_path, kb_path, vocab_path):
        """
        Load the model and its settings from a dictionary.
        """
        model_dict = torch.load(model_path)
        model = model_dict['model']
        prior = model_dict.get('prior', False)
        global_model = model_dict.get('global_model', False)
        rdf2vec = model_dict.get('rdf2vec', False)

        trainer = EntityLinkingTrainer(kb_path, vocab_path, prior=prior, global_model=global_model, rdf2vec=rdf2vec)
        trainer.model = model
        return trainer


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
        version += ".%s" % args.kb_name if args.kb_name else ""
        version += ".rdf2vec" if args.rdf2vec else ""

        model_name = "%s.%i.%iep.%ibs.%ihu.%slr.%sdo" % (version, n_samples, n_epochs, batch_size, hidden_units,
                                                         lr_str, do_str)
        model_path = settings.LINKER_MODEL_PATH + model_name + ".pt"

    # Load or train the model
    if args.load_model:
        trainer = EntityLinkingTrainer.load_model(args.load_model, kb_path, vocab_path)
    else:
        trainer = EntityLinkingTrainer(kb_path, vocab_path, prior=args.prior, global_model=args.global_model,
                                       rdf2vec=args.rdf2vec, save_best=args.save_best)
        trainer.set_model_path(model_path)

        # Build training and validation data
        logger.info("Create training (and validation) data...")
        x_train, y_train, _ = trainer.create_data(n_samples + n_val_samples)
        x_val, y_val = None, None
        if n_val_samples > 0:
            x_train, x_val = x_train[:n_samples], x_train[n_samples:]
            y_train, y_val = y_train[:n_samples], y_train[n_samples:]
        logger.info(f"Training samples size: {x_train.size()}, training labels size: {y_train.size()}")
        logger.info(f"First 20 training labels: {y_train[:20]}")

        # Train the model
        logger.info("Start training...")
        trainer.initialize_model(x_train.shape[1], hidden_units, dropout)
        trainer.train(x_train, y_train, n_epochs, batch_size, learning_rate, x_val, y_val)

        # Save the model
        trainer.save_model()

    # Build test data
    logger.info("Create test data...")
    x_test, y_test, conjugate_indices_test = trainer.create_data(n_test_samples, test=True)
    logger.info(f"Test samples size: {x_test.size()}, test labels size: {y_test.size()}")
    logger.info(f"First 20 test labels: {y_test[:20]}")

    # Test the model
    trainer.evaluate(x_test, y_test, conjugate_indices_test)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("-o", "--output_file", type=str,
                        help="Output file to write the model to. Should end on '.pt'. Per default this is"
                             "<local/global>_model_<prior/vanilla>.<dot_separated_settings>."
                             "<n_samples>.<epochs>ep.<batch_size>bs.<hidden_units>hu.<learning_rate>lr.<dropout>do.pt")

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

    parser.add_argument("-do", "--dropout", type=float, default=0,
                        help="Dropout. (Default: 0.0)")

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

    parser.add_argument("--rdf2vec", action="store_true",
                        help="Use RDF2Vec entity vectors.")

    parser.add_argument("-kb", "--kb_name", type=str, default=None, choices=["wikipedia"],
                        help="Name of the knowledgebase.")

    parser.add_argument("--load_model", type=str, default=None,
                        help="Load model from given path instead of training a new model and evaluate over it.")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main(parser.parse_args())
