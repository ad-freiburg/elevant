from yattag import Doc
from yattag import indent
import json
import threading
import webbrowser
import re
from http.server import HTTPServer,SimpleHTTPRequestHandler

config = json.load(open('config/config.json'))
outputpath = config['outputpath']

TITLE2FILENAME_PATH = outputpath + "dictionaries/title2filepath.json"
TITLE2ID_PATH = outputpath + "dictionaries/title2Id.json"
WIKILINK = 'https://en.wikipedia.org/?curid='

FILE = '../frontend.html'
PORT = 8080

title2filepath = json.load(open(TITLE2FILENAME_PATH))
title2id = json.load(open(TITLE2ID_PATH))

def process_line(line,doc, tag, text):
    while True:
        start = line.find('[[')
        end = line.find(']]')
        if start > -1 and end > -1 and start < end:
            before = line[:start]
            after = line[end+2:]
            mention = line[start+2:end]

            text(before)

            tokens = mention.split('|')
            entity = tokens[0]
            alias = tokens[1]
            type = tokens[-1]

            if entity in title2id:
                id = title2id[entity]
                link = WIKILINK + str(id)
                klass = 'annotated'
                '''if type == 'COREF':
                    klass = 'coref'
                el'''
                if type == 'RARE_ANNOTATION':
                    klass = 'annotation'
                elif type == 'ANNOTATION':
                    klass = 'annotation'
                '''elif type == 'UNKNOWN':
                    klass = 'unknown'
                elif type == 'REDIRECT':
                    klass = 'annotated'
                '''


                with tag('a',('href',link),('target','_blank'),klass=klass):
                    text(alias)
            else:
                with tag('font', ('color', 'green')):
                    text(alias)

            line = after
        else:
            break

    text(line + " ")

def create_html_paragraph(line,doc, tag, text):
    with tag('p'):
        process_line(line,doc,tag,text)

def create_html(title2filepath,title):

    doc, tag, text = Doc().tagtext()
    print('title: ' + title)
    if title not in title2filepath:
        print('title not found.')
        with tag('p'):
            text('Title not available')
    else:
        with tag('h1'):
            text(title)
        path = outputpath + "final_articles" + re.search(r"/[^/]*/[^/]*\.txt", title2filepath[title]).group(0)
        with open(path, 'r', encoding='utf8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('==='):
                    line = line.replace('=','')
                    with tag('h4'):
                        text(line)
                elif line.startswith('=='):
                    line = line.replace('=', '')
                    with tag('h2'):
                        text(line)
                else:
                    create_html_paragraph(line, doc, tag, text)

    result = indent(doc.getvalue())
    return result

class TestHandler(SimpleHTTPRequestHandler):

    def do_POST(self):
        """Handle a post request by returning the square of the number."""
        length = int(self.headers.get('content-length'))
        data_string = self.rfile.read(length).decode("utf-8")

        print('data string: ' + data_string)

        html = create_html(title2filepath,data_string)

        self.send_response(200)
        self.send_header('Content-Type', 'application/xml')
        self.end_headers()

        self.wfile.write(html.encode())


def open_browser():
    """Start a browser after waiting for half a second."""
    def _open_browser():
        webbrowser.open('http://localhost:%s/%s' % (PORT, FILE))
    thread = threading.Timer(0.5, _open_browser)
    thread.start()

def start_server():
    """Start the server."""
    server_address = ("", PORT)
    server = HTTPServer(server_address, TestHandler)
    server.serve_forever()

if __name__ == "__main__":
    open_browser()
    start_server()

