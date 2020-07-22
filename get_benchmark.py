from src.conll_benchmark import conll_documents


if __name__ == "__main__":
    for document in conll_documents():
        print(document.text())
