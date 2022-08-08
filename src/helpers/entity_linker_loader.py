from typing import Optional

import spacy
import logging

from spacy.vocab import Vocab
from spacy.language import Language
from spacy.kb import KnowledgeBase

from src import settings

logger = logging.getLogger("main." + __name__.split(".")[-1])


class EntityLinkerLoader:
    @staticmethod
    def load_trained_linker(name: str, kb_name: Optional[str] = None):
        logger.info("Loading linker model...")
        path = settings.SPACY_MODEL_DIRECTORY + name
        with open(path, "rb") as f:
            model_bytes = f.read()
        model = spacy.blank("en")
        model: Language
        pipeline = ['tagger', 'parser', 'ner', 'entity_linker']
        for pipe_name in pipeline:
            pipe = model.create_pipe(pipe_name)
            model.add_pipe(pipe)
        model.from_bytes(model_bytes)
        logger.info("-> Linker model loaded.")

        logger.info("Loading knowledge base...")
        if kb_name is None:
            vocab_path = settings.VOCAB_DIRECTORY
            kb_path = settings.KB_FILE
        else:
            load_path = settings.KB_DIRECTORY + kb_name + "/"
            vocab_path = load_path + "vocab"
            kb_path = load_path + "kb"
        vocab = Vocab().from_disk(vocab_path)
        kb = KnowledgeBase(vocab=vocab, entity_vector_length=vocab.vectors.shape[1])
        kb.load_bulk(kb_path)
        model.get_pipe("entity_linker").set_kb(kb)
        logger.info("-> Knowledge base loaded.")

        model.disable_pipes(["tagger"])

        return model

    @staticmethod
    def load_entity_linker(name: str, kb_name: Optional[str] = None):
        model = EntityLinkerLoader.load_trained_linker(name, kb_name=kb_name)
        entity_linker = model.get_pipe("entity_linker")
        return entity_linker
