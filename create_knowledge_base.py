import sys

from src.entity_database import EntityDatabase
from src.knowledge_base_creator import KnowledgeBaseCreator
from src import settings


def print_help():
    print("Usage:\n"
          "    python3 create_knowledge_pase.py <minimum_score>")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print_help()
        exit(1)

    minimum_score = int(sys.argv[1])

    entity_db = EntityDatabase()
    print("load entities...")
    entity_db.load_entities_small(minimum_score)
    print(entity_db.size_entities(), "entities")
    print("load aliases...")
    entity_db.add_name_aliases()
    entity_db.add_synonym_aliases()
    print(entity_db.size_aliases(), "aliases")
    print("load frequencies...")
    entity_db.load_mapping()
    entity_db.load_redirects()
    entity_db.load_link_frequencies()

    print("create knowledge base...")
    kb = KnowledgeBaseCreator.create_kb(entity_db=entity_db)

    print(kb.get_size_entities(), "knowledge base entities")
    print(kb.get_size_aliases(), "knowledge base aliases")

    kb.dump(settings.KB_FILE)
    print("Saved knowledge base to", settings.KB_FILE)
    kb.vocab.to_disk(settings.VOCAB_DIRECTORY)
    print("Saved vocab to", settings.VOCAB_DIRECTORY)
