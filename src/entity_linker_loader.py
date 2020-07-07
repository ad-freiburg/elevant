import spacy

from spacy.vocab import Vocab
from spacy.language import Language
from spacy.kb import KnowledgeBase

from src import settings


class EntityLinkerLoader:
    @staticmethod
    def load_trained_linker():
        print("loading model...")
        with open(settings.LINKER_DIRECTORY, "rb") as f:
            model_bytes = f.read()
        model = spacy.blank("en")
        model: Language
        pipeline = ['tagger', 'parser', 'ner', 'entity_linker']
        for pipe_name in pipeline:
            pipe = model.create_pipe(pipe_name)
            model.add_pipe(pipe)
        model.from_bytes(model_bytes)

        print("loading knowledge base...")
        vocab = Vocab().from_disk(settings.VOCAB_DIRECTORY)
        kb = KnowledgeBase(vocab=vocab, entity_vector_length=vocab.vectors.shape[1])
        kb.load_bulk(settings.KB_FILE)
        model.get_pipe("entity_linker").set_kb(kb)

        model.disable_pipes(["tagger"])

        return model

    @staticmethod
    def load_entity_linker():
        model = EntityLinkerLoader.load_trained_linker()
        entity_linker = model.get_pipe("entity_linker")
        return entity_linker
