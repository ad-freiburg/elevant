import xml.sax
import re
import os
import json
import time

current_milli_time = lambda: int(round(time.time() * 1000))

RE_LINKS = re.compile(r'\[{2}(.*?)\]{2}', re.DOTALL | re.UNICODE)

IGNORED_NAMESPACES = [
    'wikipedia', 'category', 'file', 'portal', 'template',
    'mediaWiki', 'user', 'help', 'book', 'draft', 'wikiProject',
    'special', 'talk', 'image','module'
]
"""MediaWiki namespaces that ought to be ignored."""

class WikiHandler(xml.sax.ContentHandler):
    def __init__(self,title2Id,id2Title,redirects):
        self.tag = ""
        self.content = ''
        self.title = ''
        self.id = -1
        self.title2Id = title2Id
        self.id2Title = id2Title
        self.redirects = redirects
        self.counter_all = 0
        self.attributes = {}
        self.n = 0
        self.start = current_milli_time()

    # Call when an element starts
    def startElement(self, tag, attributes):
        self.tag = tag
        self.attributes = attributes

    # Call when an elements ends
    def endElement(self, tag):
        if tag == 'title':
            self.title = self.content.strip()
        elif tag == 'id':
            self.id = int(self.content)
            if self.title not in self.title2Id:
                self.title2Id[self.title] = self.id
                self.id2Title[self.id] = self.title
                self.counter_all += 1

                if self.counter_all % 1000 == 0:
                    diff = current_milli_time() - self.start
                    print('Pages processed: ' + str(self.counter_all) + ', avg t: ' + str(diff / self.counter_all), end='\r')
        elif tag == 'text':
            self.n += 1
            if not any(self.title.lower().startswith(ignore + ':') for ignore in IGNORED_NAMESPACES) and not self.title.lower().startswith('list of'):
                self.processArticle()
        elif tag == 'redirect' and 'title' in self.attributes:
            redirect = self.attributes['title']
            if not any(self.title.lower().startswith(ignore + ':') for ignore in IGNORED_NAMESPACES) \
                    and not any(redirect.lower().startswith(ignore + ':') for ignore in IGNORED_NAMESPACES) \
                    and not redirect.lower().startswith('list of') \
                    and not self.title.lower().startswith('list of'):

                self.redirects[self.title] = redirect

        self.content = ""

    # Call when a character is read
    def characters(self, content):
        self.content += content

    def processArticle(self):
        text = self.content.strip()
        #self.title2Id[self.title] = self.id
        if text.lower().startswith('#redirect'):
            match = re.search(RE_LINKS,text)
            if match:
                redirect = match.group(1).strip()
                pos_bar = redirect.find('|')
                if pos_bar > -1:
                    redirect = redirect[:pos_bar]
                redirect = redirect.replace('_',' ')
                if not any(redirect.lower().startswith(ignore + ':') for ignore in IGNORED_NAMESPACES) and not redirect.lower().startswith('list of'):
                    self.redirects[self.title] = redirect
        else:
            lines = text.split('\n')
            for line in lines:
                if not line.startswith('{{redirect|'):
                    break
                else:
                    line = line[11:]
                    line = line[:line.find('|')]
                    if len(line) > 0:
                        if not any(line.lower().startswith(ignore + ':') for ignore in IGNORED_NAMESPACES) and not line.lower().startswith('list of'):
                            self.redirects[line] = self.title

if (__name__ == "__main__"):

    title2Id = {}
    id2Title = {}
    redirects = {}

    config = json.load(open('config/config.json'))

    wikipath = config['wikipath']
    outputpath = config['outputpath']
    dictionarypath = outputpath + 'dictionaries/'

    mode = 0o755
    os.mkdir(outputpath, mode)
    os.mkdir(dictionarypath, mode)


    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)
    Handler = WikiHandler(title2Id,id2Title,redirects)
    parser.setContentHandler(Handler)
    parser.parse(wikipath)
    print('done')

    with open(dictionarypath + 'title2Id.json', 'w') as f:
        json.dump(title2Id, f)
    with open(dictionarypath + 'id2Title.json', 'w') as f:
        json.dump(id2Title, f)
    with open(dictionarypath + 'redirects.json', 'w') as f:
        json.dump(redirects, f)
