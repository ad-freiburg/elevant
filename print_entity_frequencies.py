from src.entity_database import EntityDatabase


if __name__ == "__main__":
    print("reading entity database...")
    entity_db = EntityDatabase()
    entity_db.load_entities_small(minimum_score=10)
    entity_db.load_mapping()
    entity_db.load_redirects()
    entity_db.add_link_aliases()
    entity_db.load_link_frequencies()

    print("counting frequencies...")
    entity_frequencies = {entity_id: 0 for entity_id in entity_db.entities}
    for alias in entity_db.aliases:
        for entity_id in entity_db.get_candidates(alias):
            frequency = entity_db.get_link_frequency(alias, entity_id)
            entity_frequencies[entity_id] += frequency

    for frequency, entity_id in sorted([(entity_frequencies[entity_id], entity_id) for entity_id in entity_frequencies],
                                       reverse=True):
        print("\t".join((entity_id, entity_db.get_entity(entity_id).name, str(frequency))))
