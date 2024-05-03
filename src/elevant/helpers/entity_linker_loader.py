from typing import Optional

import spacy
import logging

from elevant import settings

logger = logging.getLogger("main." + __name__.split(".")[-1])


class EntityLinkerLoader:
    @staticmethod
    def load_trained_linker(name: str, kb_name: Optional[str] = None):
        logger.info("Loading linker model...")

        model = spacy.load("en_core_web_lg")

        # Load the previously saved entity linker
        path = settings.SPACY_MODEL_DIRECTORY + name
        model.add_pipe("entity_linker")
        model.get_pipe("entity_linker").from_disk(path)

        logger.info("-> Linker model loaded.")

        return model

    @staticmethod
    def load_entity_linker(name: str, kb_name: Optional[str] = None):
        model = EntityLinkerLoader.load_trained_linker(name, kb_name=kb_name)
        entity_linker = model.get_pipe("entity_linker")
        return entity_linker
