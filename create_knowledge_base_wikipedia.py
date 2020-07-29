from src.knowledge_base_creator import KnowledgeBaseCreator
from src import settings


if __name__ == "__main__":
    kb = KnowledgeBaseCreator.create_kb_wikipedia()
    print(kb.get_size_entities(), "knowledge base entities")
    print(kb.get_size_aliases(), "knowledge base aliases")

    kb_path = settings.KB_DIRECTORY + "wikipedia/"
    kb.dump(kb_path)
    print("Saved knowledge base to", kb_path)
    vocab_file = kb_path + "vocab"
    kb.vocab.to_disk(vocab_file)
    print("Saved vocab to", vocab_file)
