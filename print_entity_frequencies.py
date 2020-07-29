from src.entity_database import EntityDatabase


if __name__ == "__main__":
    print("reading entity database...")
    entity_db = EntityDatabase()
    entity_db.load_entities_big()
    entity_db.load_mapping()
    entity_db.load_redirects()
    entity_db.add_link_aliases()
    entity_db.load_link_frequencies()

    print("counting frequencies...")
    entity_frequencies = {entity_id: 0 for entity_id in entity_db.entities}
    total = 0
    for alias in entity_db.aliases:
        for entity_id in entity_db.get_candidates(alias):
            frequency = entity_db.get_link_frequency(alias, entity_id)
            entity_frequencies[entity_id] += frequency
            total += frequency

    accumulated = 0
    for i, (frequency, entity_id) in enumerate(sorted([(entity_frequencies[entity_id], entity_id)
                                                       for entity_id in entity_frequencies],
                                               reverse=True)):
        accumulated += frequency
        coverage = accumulated / total
        print("\t".join((str(i + 1),
                         entity_id,
                         entity_db.get_entity(entity_id).name,
                         str(frequency),
                         "%.2f" % (coverage * 100))))
