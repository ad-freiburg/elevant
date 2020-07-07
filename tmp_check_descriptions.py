from create_knowledge_base import ABSTRACTS_FILE


if __name__ == "__main__":
    entity_ids = set()
    for line in open(ABSTRACTS_FILE):
        entity_id, name, description = line[:-1].split('\t')
        if entity_id in entity_ids:
            print("duplicate:", entity_id)
        entity_ids.add(entity_id)