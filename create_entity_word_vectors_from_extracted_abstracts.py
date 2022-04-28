import os
import pickle

from src.helpers.word_vectors import VectorGenerator
from src.models.entity_database import EntityDatabase
from src import settings


if __name__ == "__main__":
    SAVE_EVERY = 10000

    entity_db = EntityDatabase()
    entity_db.load_all_entities_in_wikipedia()
    entity_db.load_wikipedia_wikidata_mapping()
    entity_db.load_redirects()
    entity_db.load_link_frequencies()

    vector_generator = VectorGenerator()

    vector_dir = settings.VECTORS_ABSTRACTS_DIRECTORY
    if not os.path.exists(vector_dir):
        os.mkdir(vector_dir)

    abstracts_file = settings.WIKIPEDIA_ABSTRACTS_FILE
    vectors = []
    file_no = 0

    for i, line in enumerate(open(abstracts_file)):
        #print("\r%i lines read" % i, end="")
        article_id, title, url, abstract = line[:-1].split("\t")
        if title in entity_db.wikipedia2wikidata:
            entity_id = entity_db.wikipedia2wikidata[title]
            if entity_db.get_entity_frequency(entity_id) > 0:
                vector = vector_generator.get_vector(abstract)
                print(entity_id, title, len(abstract), vector.shape)
                vectors.append((entity_id, vector))
                if len(vectors) == SAVE_EVERY:
                    save_path = vector_dir + "%i.pkl" % file_no
                    with open(save_path, "wb") as save_file:
                        pickle.dump(vectors, save_file)
                    print("Saved %i vectors to %s" % (len(vectors), save_path))
                    file_no += 1
                    vectors = []
    if len(vectors) > 0:
        save_path = vector_dir + "%i.pkl" % file_no
        with open(save_path, "wb") as save_file:
            pickle.dump(vectors, save_file)
        print("Saved %i vectors to %s" % (len(vectors), save_path))
