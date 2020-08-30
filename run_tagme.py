from src.tagme_linker import TagMeLinker


if __name__ == "__main__":
    linker = TagMeLinker()

    while True:
        text = input("> ")
        linker.predict(text)
