import logging
import spacy
from spacy.kb import KnowledgeBase

from elevant.models.entity_database import EntityDatabase
from elevant.helpers.word_vectors import VectorLoader
from elevant import settings

logger = logging.getLogger("main." + __name__.split(".")[-1])


class KnowledgeBaseCreator:
    @staticmethod
    def create_kb_wikipedia() -> KnowledgeBase:
        logger.info("Load entity database ...")
        entity_db = EntityDatabase()
        entity_db.load_wikipedia_to_wikidata_db()
        entity_db.load_redirects()
        entity_db.load_link_aliases(with_frequencies=True)
        entity_db.load_entity_frequencies()
        logger.info("-> Entity database loaded.")

        logger.info("Load Spacy model...")
        model = spacy.load(settings.LARGE_MODEL_NAME)
        kb = KnowledgeBase(vocab=model.vocab, entity_vector_length=model.vocab.vectors.shape[1])
        logger.info("-> Spacy model loaded.")

        logger.info("Load vectors...")
        vector_dir = settings.VECTORS_DIRECTORY
        for entity_id, vector in VectorLoader.iterate(vector_dir):
            frequency = entity_db.get_entity_frequency(entity_id)
            kb.add_entity(entity=entity_id, freq=frequency, entity_vector=vector)
        logger.info("-> Vectors loaded. Knowledge base contains %d entities." % len(kb))

        logger.info("Adding aliases...")
        for alias in entity_db.link_aliases:
            if len(alias) > 0:
                alias_entity_ids = [entity_id for entity_id in entity_db.get_candidates(alias)
                                    if kb.contains_entity(entity_id)]
                if len(alias_entity_ids) > 0:
                    frequencies = []
                    for entity_id in alias_entity_ids:
                        frequency = entity_db.get_link_frequency(alias, entity_id)
                        frequencies.append(frequency)
                    sum_frequencies = sum(frequencies)
                    if sum_frequencies > 0:
                        probabilities = [frequency / sum_frequencies for frequency in frequencies]
                    else:
                        probabilities = [1 / len(alias_entity_ids) for _ in alias_entity_ids]
                    kb.add_alias(alias=alias, entities=alias_entity_ids, probabilities=probabilities)
        logger.info("-> %d aliases added." % kb.get_size_aliases())

        return kb

    @staticmethod
    def create_kb(entity_db: EntityDatabase) -> KnowledgeBase:
        model = spacy.load(settings.LARGE_MODEL_NAME)
        kb = KnowledgeBase(vocab=model.vocab, entity_vector_length=model.vocab.vectors.shape[1])

        logger.info("Loading entity vectors...")
        for entity_id, vector in VectorLoader.iterate():
            if entity_db.contains_entity(entity_id) and not kb.contains_entity(entity_id):
                score = entity_db.get_sitelink_count(entity_id)
                kb.add_entity(entity=entity_id, freq=score, entity_vector=vector)
        logger.info("-> Vectors loaded. Knowledge base contains %d entities." % len(kb))

        logger.info("Adding aliases...")
        for alias in entity_db.aliases:
            if len(alias) > 0:
                alias_entity_ids = [entity_id for entity_id in entity_db.get_candidates(alias)
                                    if kb.contains_entity(entity_id)]
                if len(alias_entity_ids) > 0:
                    frequencies = []
                    for entity_id in alias_entity_ids:
                        frequency = entity_db.get_link_frequency(alias, entity_id)
                        frequencies.append(frequency)
                    sum_frequencies = sum(frequencies)
                    if sum_frequencies > 0:
                        probabilities = [frequency / sum_frequencies for frequency in frequencies]
                    else:
                        probabilities = [1 / len(alias_entity_ids) for _ in alias_entity_ids]
                    kb.add_alias(alias=alias, entities=alias_entity_ids, probabilities=probabilities)
        logger.info("-> %d aliases added." % kb.get_size_aliases())

        return kb
