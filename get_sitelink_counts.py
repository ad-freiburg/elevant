from src.settings import DATA_DIRECTORY


if __name__ == "__main__":
    input_file = DATA_DIRECTORY + "wikidata_mappings/wikidata_scores.txt"
    with open(input_file) as f:
        for line in f:
            line = line[:-1]
            columns = line.split("\t")
            qid = columns[0][:-1].split("/")[-1]
            link_count = int(columns[2].split("\"")[1])
            print(qid, link_count)
