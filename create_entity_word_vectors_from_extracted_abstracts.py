import os

from src.word_vectors import VectorGenerator
from src.entity_database import EntityDatabase
from src import settings


if __name__ == "__main__":
    SAVE_EVERY = 10000

    entity_db = EntityDatabase()
    entity_db.load_entities_big()
    entity_db.load_mapping()
    entity_db.load_redirects()
    entity_db.load_link_frequencies()

    vector_generator = VectorGenerator()

    vector_dir = settings.DATA_DIRECTORY + "vectors_abstracts/"
    if not os.path.exists(vector_dir):
        os.mkdir(vector_dir)

    abstracts_file = settings.DATA_DIRECTORY + "article_abstracts.txt"
    vectors = []
    file_no = 0

    for i, line in enumerate(open(abstracts_file)):
        print("\r%i lines read" % i, end="")
        article_id, title, url, abstract = line[:-1].split("\t")
        if article_id in entity_db.wikipedia2wikidata:
            entity_id = entity_db.wikipedia2wikidata[article_id]
            if entity_db.get_entity_frequency(entity_id) > 0:
                vector = vector_generator.get_vector(abstract)
                print()
                print(entity_id, title, vector.shape)
                #vectors.append()
