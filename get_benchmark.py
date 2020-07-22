from src import settings


def get_token(raw: str) -> str:
    return raw.split("\\")[0]


def parse_article(raw: str) -> str:
    id, text = raw.split("\t")
    tokens = [get_token(raw_token) for raw_token in text.split()]
    return ' '.join(tokens)


if __name__ == "__main__":
    for line in open(settings.CONLL_BENCHMARK_FILE):
        line = line[:-1]
        text = parse_article(line)
        print(text)
