import sys
import pickle

from src.entity_database_reader import EntityDatabaseReader
from src.word_vectors import VectorGenerator
from src import settings


def preprocess_description(description: str) -> str:
    if description.startswith("{"):
        split = description.split("}")
        return split[1] if len(split) > 1 else description
    return description


def save_vectors(vectors, file_no):
    path = settings.VECTORS_DIRECTORY + "%i.pkl" % file_no
    print("\nsaving vectors to %s" % path)
    with open(path, "wb") as f:
        pickle.dump(vectors, f)


SAVE_EVERY = 10000


if __name__ == "__main__":
    minimum_score = int(sys.argv[1])
    start_line = 0 if len(sys.argv) == 2 else int(sys.argv[2])

    entity_db = EntityDatabaseReader.read_entity_database(minimum_score=minimum_score)
    generator = VectorGenerator()

    print("generating vectors...")
    vectors = []
    file_no = start_line // SAVE_EVERY
    for i, line in enumerate(open(settings.ABSTRACTS_FILE)):
        if i < start_line:
            continue
        entity_id, name, description = line[:-1].split('\t')
        if entity_db.contains(entity_id):
            description = preprocess_description(description)
            vector = generator.get_vector(description)
            vectors.append((entity_id, vector))
            print("\r%i vectors" % len(vectors), end='')
            if len(vectors) == SAVE_EVERY:
                save_vectors(vectors, file_no)
                file_no += 1
                vectors = []
    print()

    if len(vectors) > 0:
        save_vectors(vectors, file_no)
