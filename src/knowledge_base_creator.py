import spacy
from spacy.kb import KnowledgeBase

from src.entity_database import EntityDatabase
from src.word_vectors import VectorLoader
from src import settings


class KnowledgeBaseCreator:
    @staticmethod
    def create_kb_wikipedia() -> KnowledgeBase:
        print("read entity database...")
        entity_db = EntityDatabase()
        entity_db.load_entities_big()
        entity_db.load_mapping()
        entity_db.load_redirects()
        entity_db.load_link_frequencies()
        entity_db.add_link_aliases()

        print("load model...")
        model = spacy.load(settings.LARGE_MODEL_NAME)
        kb = KnowledgeBase(vocab=model.vocab, entity_vector_length=model.vocab.vectors.shape[1])

        print("read vectors...")
        vector_dir = settings.DATA_DIRECTORY + "vectors_abstracts/"
        for entity_id, vector in VectorLoader.iterate(vector_dir):
            frequency = entity_db.get_entity_frequency(entity_id)
            kb.add_entity(entity=entity_id, freq=frequency, entity_vector=vector)
        print(len(kb), "entities")

        print("add aliases...")
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
        print(kb.get_size_aliases(), "aliases")

        return kb

    @staticmethod
    def create_kb(entity_db: EntityDatabase) -> KnowledgeBase:
        model = spacy.load(settings.LARGE_MODEL_NAME)
        kb = KnowledgeBase(vocab=model.vocab, entity_vector_length=model.vocab.vectors.shape[1])

        print("reading entity vectors...")
        for entity_id, vector in VectorLoader.iterate():
            if entity_db.contains_entity(entity_id) and not kb.contains_entity(entity_id):
                score = entity_db.get_score(entity_id)
                kb.add_entity(entity=entity_id, freq=score, entity_vector=vector)
                # print("\r%i entities" % len(kb), end='')
        # print()
        print(len(kb), "entities")

        print("adding aliases...")
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
                    # print(alias, list(zip(alias_entity_ids, probabilities)))
                    kb.add_alias(alias=alias, entities=alias_entity_ids, probabilities=probabilities)
        print(kb.get_size_aliases(), "aliases")

        return kb
