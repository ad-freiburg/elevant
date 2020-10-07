from src.models.entity_database import EntityDatabase
from src import settings


if __name__ == "__main__":
    print("load entities...")
    entity_db = EntityDatabase()
    entity_db.load_entities_big()
    print("load frequencies...")
    entity_db.load_mapping()
    entity_db.load_redirects()
    entity_db.load_link_frequencies()

    print("read descriptions...")
    entities_with_description = set()
    for line in open(settings.ABSTRACTS_FILE):
        entity_id, name, description = line[:-1].split('\t')
        entities_with_description.add(entity_id)

    frequency_id_pairs = sorted([(entity_db.get_entity_frequency(entity_id), entity_id)
                                 for entity_id in entity_db.entities],
                                reverse=True)
    total = sum(frequency for frequency, id in frequency_id_pairs)
    uncovered = 0
    n_entities_without_description = 0

    for i, (frequency, entity_id) in enumerate(frequency_id_pairs):
        if frequency > 0:
            if entity_id not in entities_with_description:
                print("\t".join((
                    str(i + 1),
                    entity_id,
                    entity_db.get_entity(entity_id).name,
                    str(frequency)
                )))
                n_entities_without_description += 1
                uncovered += frequency

    print("%i entities without description" % n_entities_without_description)
    print("%.2f %% mentions uncovered" % (uncovered / total * 100))
