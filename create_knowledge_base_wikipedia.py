import os

from src.knowledge_base_creator import KnowledgeBaseCreator
from src import settings


if __name__ == "__main__":
    kb = KnowledgeBaseCreator.create_kb_wikipedia()
    print(kb.get_size_entities(), "knowledge base entities")
    print(kb.get_size_aliases(), "knowledge base aliases")

    if not os.path.exists(settings.KB_DIRECTORY):
        os.mkdir(settings.KB_DIRECTORY)

    save_path = settings.KB_DIRECTORY + "wikipedia/"
    if not os.path.exists(save_path):
        os.mkdir(save_path)

    kb_path = save_path + "kb"
    kb.dump(kb_path)
    print("Saved knowledge base to", kb_path)
    vocab_file = save_path + "vocab"
    kb.vocab.to_disk(vocab_file)
    print("Saved vocab to", vocab_file)
