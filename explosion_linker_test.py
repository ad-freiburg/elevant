from src.linkers.explosion_linker import ExplosionEntityLinker


if __name__ == "__main__":
    path = "/home/hertel/explosion/projects/nel-wikipedia/linker/nlp"
    linker = ExplosionEntityLinker(path)

    while True:
        text = input("> ")
        predictions = linker.predict(text)
        for span in predictions:
            prediction = predictions[span]
            snippet = text[span[0]:span[1]]
            print(span, snippet, prediction.entity_id, len(prediction.candidates))
