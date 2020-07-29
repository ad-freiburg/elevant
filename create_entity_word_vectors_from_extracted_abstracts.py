

from src.word_vectors import VectorGenerator
from src.entity_database import EntityDatabase
from src import settings


if __name__ == "__main__":
    entity_db = EntityDatabase()
    entity_db.load_entities_big()
    entity_db.load_mapping()
    entity_db.load_redirects()
    entity_db.load_link_frequencies()

    vector_generator = VectorGenerator()

    abstracts_file = settings.DATA_DIRECTORY + "article_abstracts.txt"
    for line in open(abstracts_file):
        article_id, title, url, abstract = line[:-1].split("\t")
        if article_id in entity_db.wikipedia2wikidata:
            entity_id = entity_db.wikipedia2wikidata[article_id]
            if entity_db.get_entity_frequency(entity_id) > 0:
                vector = vector_generator.get_vector(abstract)
                print(entity_id, title, vector.shape)
