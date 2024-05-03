import argparse
import sys
import os
from rdflib import Graph

sys.path.append(".")

from elevant import settings
from elevant.utils import log


def main(args):
    logger.info(f"Creating mappings from {args.input_file} ...")
    graph = Graph()
    graph.parse(args.input_file, format='ttl')

    # Check if the directory for the custom mappings exist and if not create it
    dirnames = [os.path.dirname(settings.CUSTOM_ENTITY_TO_NAME_FILE),
                os.path.dirname(settings.CUSTOM_ENTITY_TO_TYPES_FILE),
                os.path.dirname(settings.CUSTOM_WHITELIST_TYPES_FILE)]
    for dirname in dirnames:
        if not os.path.exists(dirname):
            logger.info(f"Creating directory {dirname}")
            os.makedirs(dirname)

    entity_to_name = {}
    entity_to_types = {}
    all_entity_types = {}
    for subj, pred, obj in graph:
        subj, pred, obj = str(subj), str(pred), str(obj)

        if pred == args.name_predicate:
            entity_to_name[subj] = obj
        elif pred == args.type_predicate:
            if subj in entity_to_types:
                entity_to_types[subj].append(obj)
            else:
                entity_to_types[subj] = [obj]
            if obj not in all_entity_types:
                all_entity_types[obj] = ""

    for t in all_entity_types.keys():
        if t in entity_to_name:
            all_entity_types[t] = entity_to_name[t]
        else:
            all_entity_types[t] = "OTHER"

    with open(settings.CUSTOM_ENTITY_TO_NAME_FILE, "w", encoding="utf8") as file:
        for entity_id, name in entity_to_name.items():
            file.write(f"{entity_id}\t{name}\n")

    with open(settings.CUSTOM_ENTITY_TO_TYPES_FILE, "w", encoding="utf8") as file:
        for entity_id, types in entity_to_types.items():
            file.write(f"{entity_id}")
            for typ in types:
                file.write(f"\t{typ}")
            file.write("\n")

    with open(settings.CUSTOM_WHITELIST_TYPES_FILE, "w", encoding="utf8") as file:
        for type_id, name in all_entity_types.items():
            file.write(f"{type_id}\t{name}\n")

    logger.info(f"Wrote {len(entity_to_name)} entity to name mappings to {settings.CUSTOM_ENTITY_TO_NAME_FILE} "
                f"and {len(entity_to_types)} entity to types mappings to {settings.CUSTOM_ENTITY_TO_TYPES_FILE} "
                f"and {len(all_entity_types)} entity types to {settings.CUSTOM_WHITELIST_TYPES_FILE}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=__doc__)

    parser.add_argument("input_file", type=str,
                        help="Input ttl file that contains the custom knowledge base or ontology.")

    parser.add_argument("--name_predicate", type=str, default="http://www.w3.org/2004/02/skos/core#prefLabel",
                        help="The predicate used to indicate the entity name.")
    parser.add_argument("--type_predicate", type=str, default="http://www.w3.org/2000/01/rdf-schema#subClassOf",
                        help="The predicate used to indicate the entity type.")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main(parser.parse_args())
