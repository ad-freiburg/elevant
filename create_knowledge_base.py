import sys

from src.entity_database_reader import EntityDatabaseReader
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

    entity_db = EntityDatabaseReader.read_entity_database(minimum_score=minimum_score)

    kb = KnowledgeBaseCreator.create_kb(entity_db=entity_db, include_link_aliases=True)

    print(kb.get_size_entities(), "knowledge base entities")
    print(kb.get_size_aliases(), "knowledge base aliases")

    kb.dump(settings.KB_FILE)
    print("Saved knowledge base to", settings.KB_FILE)
    kb.vocab.to_disk(settings.VOCAB_DIRECTORY)
    print("Saved vocab to", settings.VOCAB_DIRECTORY)
