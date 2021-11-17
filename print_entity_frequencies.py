from src.models.entity_database import EntityDatabase


if __name__ == "__main__":
    print("reading entity database...")
    entity_db = EntityDatabase()
    entity_db.load_entities_big()
    entity_db.load_wikipedia_wikidata_mapping()
    entity_db.load_redirects()
    entity_db.load_link_frequencies()

    frequency_id_pairs = sorted([(entity_db.get_entity_frequency(entity_id), entity_id)
                                 for entity_id in entity_db.entities],
                                reverse=True)
    total = sum(frequency for frequency, id in frequency_id_pairs)

    accumulated = 0
    for i, (frequency, entity_id) in enumerate(frequency_id_pairs):
        accumulated += frequency
        coverage = accumulated / total
        print("\t".join((str(i + 1),
                         entity_id,
                         entity_db.get_entity(entity_id).name,
                         str(frequency),
                         "%.2f" % (coverage * 100))))
