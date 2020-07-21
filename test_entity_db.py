import sys

from src.entity_database_new import EntityDatabase


if __name__ == "__main__":
    big = sys.argv[1] == "big"
    entity_db = EntityDatabase()
    print("load entities...")
    if big:
        entity_db.load_entities_big()
    else:
        entity_db.load_entities_small()
    print(entity_db.size_entities(), "entities")
    """print("load synonyms...")
    entity_db.add_synonym_aliases()
    print(entity_db.size_aliases(), "aliases")
    print("load names...")
    entity_db.add_name_aliases()
    print(entity_db.size_aliases(), "aliases")"""
    print("load mapping...")
    entity_db.load_mapping()
    print("load redirects...")
    entity_db.load_redirects()
    print("load link aliases...")
    entity_db.add_link_aliases()
    print(entity_db.size_aliases(), "aliases")
    print("load frequencies...")
    entity_db.load_link_frequencies()
    while True:
        text = input("> ")
        for candidate_id in sorted(entity_db.get_candidates(text)):
            entity_name = entity_db.get_entity(candidate_id).name
            frequency = entity_db.get_link_frequency(text, candidate_id)
            print(candidate_id, entity_name, frequency)
