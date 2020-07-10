import re


def preprocess(line: str) -> str:
    line = line.strip()
    line = re.sub("\[[0-9]*\]", "", line)
    line = line.replace("[citation needed]", "")
    return line


if __name__ == "__main__":
    path = "/home/hertel/wikipedia/wikipedia_2020-06-08/libya_raw.txt"
    for line in open(path):
        line = preprocess(line[:-1])
        if len(line) > 0:
            print(line)
