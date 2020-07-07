import spacy
from spacy.kb import KnowledgeBase
import pickle

from src.entity_database import EntityDatabase
from src.word_vectors import VectorLoader
from src import settings


class KnowledgeBaseCreator:
    @staticmethod
    def create_kb(entity_db: EntityDatabase,
                  include_link_aliases: bool) -> KnowledgeBase:
        model = spacy.load(settings.LARGE_MODEL_NAME)
        kb = KnowledgeBase(vocab=model.vocab, entity_vector_length=model.vocab.vectors.shape[1])

        print("reading entity vectors...")
        for entity_id, vector in VectorLoader.iterate():
            if entity_db.contains(entity_id) and not kb.contains_entity(entity_id):
                score = entity_db.get_score(entity_id)
                kb.add_entity(entity=entity_id, freq=score, entity_vector=vector)
                # print("\r%i entities" % len(kb), end='')
        # print()
        print(len(kb), "entities")

        print("reading aliases from database...")
        aliases = {}  # alias -> {entity_id -> count}
        for alias in entity_db.all_aliases():
            aliases[alias] = {entity_id: 1 for entity_id in entity_db.get_candidates(alias)}

        if include_link_aliases:
            print("reading aliases from link frequencies...")
            with open(settings.LINK_COUNTS_FILE, "rb") as f:
                link_aliases = pickle.load(f)
                for alias in link_aliases:
                    if alias not in aliases:
                        aliases[alias] = dict()
                    for entity_id in link_aliases[alias]:
                        count = link_aliases[alias][entity_id]
                        if entity_id not in aliases[alias]:
                            aliases[alias][entity_id] = count
                        else:
                            aliases[alias][entity_id] += count

        print("adding aliases...")
        for alias in sorted(aliases):
            alias_entity_ids = [entity_id for entity_id in aliases[alias] if kb.contains_entity(entity_id)]
            if len(alias_entity_ids) > 0 and len(alias) > 0:
                frequencies = [aliases[alias][entity_id] for entity_id in alias_entity_ids]
                sum_frequencies = sum(frequencies)
                probabilities = [frequency / sum_frequencies for frequency in frequencies]
                kb.add_alias(alias=alias, entities=alias_entity_ids, probabilities=probabilities)
        print(kb.get_size_aliases(), "aliases")

        return kb
