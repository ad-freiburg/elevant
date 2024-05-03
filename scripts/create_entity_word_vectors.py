import argparse
import sys
import pickle

sys.path.append(".")

from elevant import settings
from elevant.utils import log
from elevant.models.entity_database import EntityDatabase
from elevant.helpers.word_vectors import VectorGenerator


def preprocess_description(description: str) -> str:
    if description.startswith("{"):
        split = description.split("}")
        return split[1] if len(split) > 1 else description
    return description


def save_vectors(vectors, file_no):
    path = settings.VECTORS_DIRECTORY + "vectors%i.pkl" % file_no
    logger.info("Saving vectors to %s" % path)
    with open(path, "wb") as f:
        pickle.dump(vectors, f)


SAVE_EVERY = 10000


def main(args):
    minimum_score = args.min_score
    start_line = args.start_line

    logger.info("Loading entity database ...")
    entity_db = EntityDatabase()
    entity_db.load_all_entities_in_wikipedia(minimum_sitelink_count=minimum_score)
    generator = VectorGenerator()

    abstracts_file = settings.QID_TO_ABSTRACTS_FILE
    vectors = []
    file_no = start_line // SAVE_EVERY
    logger.info("Generating vectors from %s ..." % abstracts_file)
    for i, line in enumerate(open(abstracts_file)):
        if i < start_line:
            continue
        entity_id, name, description = line[:-1].split('\t')
        if entity_db.contains_entity(entity_id):
            description = preprocess_description(description)
            vector = generator.get_vector(description)
            vectors.append((entity_id, vector))
            print("\r%i vectors" % len(vectors), end='')
            if len(vectors) == SAVE_EVERY:
                print()
                save_vectors(vectors, file_no)
                file_no += 1
                vectors = []
    print()

    if len(vectors) > 0:
        save_vectors(vectors, file_no)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("min_score", type=int,
                        help="Minimum score.")
    parser.add_argument("--start_line", type=int, default=0,
                        help="Start line.")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main(parser.parse_args())
