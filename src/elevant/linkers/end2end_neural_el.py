import requests
import json


def query(text):
    ## Takes the input string and passes it to the service and gets the reponse back.
    myjson = {"text": text, "spans": []}
    r = requests.post("http://localhost:5555", json=myjson)
    return json.loads(r.content)


def format_index_output(text):
    ## main function which sends the input text to the service, gets the response back and formats the output
    ## in a presentable form to evaluate.

    ents = query(text)
    ents.sort(key=lambda tup: tup[0], reverse=True)
    for i, ent in enumerate(ents):
        text = text[:ent[0]] + '[' + text[ent[0]:ent[0] + ent[1]] + '](https://en.wikipedia.org/wiki/' + ent[
            2] + ')' + text[ent[0] + ent[1]:]

    print(text)
