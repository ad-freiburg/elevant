from src import settings


class TypeExtractor:
    def __init__(self):
        self.entity_to_categories = {}
        self.entity_to_relevant_types = {}

    def load_entity_to_categories(self, mappings_file: str = settings.TYPE_MAPPING_FILE):
        with open(mappings_file, "r") as file:
            for line in file:
                line = line[:-1]
                entity_id, primary, secondary = line.split("\t")
                primary_id = primary.split(":")[0]
                secondary_id = secondary.split(":")[0]
                self.entity_to_categories[entity_id] = (primary_id, secondary_id)

    def extract_relevant_types(self, mapping_file: str = settings.ALL_TYPES_FILE):
        """
        Extract all classes of an entity that come before its secondary category
        in the class hierarchy.
        If no secondary type exists, extract all classes up until two levels
        below the highest level (which is usually the class 'entity').
        """
        with open(mapping_file, "r") as file:
            for line in file:
                line = line[:-1]
                lst = line.split("\t")
                if len(lst) < 2:
                    continue
                entity_id = lst[0]
                secondary_id = None
                if entity_id in self.entity_to_categories:
                    secondary_id = self.entity_to_categories[entity_id][1]
                highest_level = int(lst[-1].split(":")[0])
                max_level = highest_level
                for el in lst[1:]:
                    level, type_id = el.split(":")
                    level = int(level)
                    if level > min(max_level, 3):
                        break
                    if secondary_id and type_id == secondary_id:
                        max_level = level
                    elif not secondary_id and level > highest_level - 2:
                        max_level = level
                    if entity_id not in self.entity_to_relevant_types:
                        self.entity_to_relevant_types[entity_id] = []
                    self.entity_to_relevant_types[entity_id].append(type_id)

    def write_relevant_types(self, outfile: str = settings.RELEVANT_TYPES_FILE):
        with open(outfile, "w", encoding="utf8") as outfile:
            for entity_id, types in sorted(self.entity_to_relevant_types.items()):
                outfile.write("%s\t" % entity_id)
                for i, cl in enumerate(types):
                    outfile.write("%s" % cl)
                    if i < len(types) - 1:
                        outfile.write(";")
                outfile.write("\n")


if __name__ == "__main__":
    extractor = TypeExtractor()
    print("Load entity to category mapping...")
    extractor.load_entity_to_categories()
    print("Extract relevant types...")
    extractor.extract_relevant_types()
    print("Write relevant types...")
    extractor.write_relevant_types()
