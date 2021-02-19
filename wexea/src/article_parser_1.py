import xml.sax
import re
import os
import json
import glob
import time
import unidecode

current_milli_time = lambda: int(round(time.time() * 1000))

RE_LINKS_1 = re.compile(r'\[{2}([^][]*)\]{2}', re.DOTALL | re.UNICODE)
RE_LINKS_2 = re.compile(r'\[{2}(.*?)\]{2}', re.DOTALL | re.UNICODE)
RE_LINKS_DISAMBIGUATION = re.compile(r'\* \[{2}(.*?)\]{2}', re.DOTALL | re.UNICODE)
RE_REMOVE_SECTIONS = re.compile(r'==\s*See also|==\s*References|==\s*Bibliography|==\s*Sources|==\s*Further Reading',
                                re.DOTALL | re.UNICODE)
RE_FILES = re.compile(r'\[\[(Image|File)(.*)\n?', re.UNICODE)

RE_PARANTHESES = re.compile(r'[\((.*?)\)]', re.UNICODE)

RE_DISAMBIGUATIONS = '{{set index article}}|{{SIA}}|{{disambiguation\||\|disambiguation}}|{{disambiguation}}|{{disamb}}|{{disambig}}|{{disamb\||\|disamb}}|{{disambig\||\|disambig}}|{{dab\||\|dab}}|{{dab}}|{{disambiguation cleanup}}'
RE_HUMAN_DISAMBIGUATIONS = '{{hndis\||\|hndis}}|{{hndis}}|{{human name disambiguation}}|{{human name disambiguation\||\|human name disambiguation}}'
RE_GEO_DISAMBIGUATIONS = '{{place name disambiguation}}|{{geodis}}|{{geodis\||\|geodis}}'
RE_NUMBER_DISAMBIGUATIONS = '{{number disambiguation\||\|number disambiguation}}|{{numdab\||\|numdab}}|{{numberdis\||\|numberdis}}|{{numberdis}}|{{numdab}}|{{number disambiguation}}'
RE_STUB = 'stub}}'

GIVEN_NAMES = '{{given name}}', '[[Category:Given names]]', '[[Category:Masculine given names]]', '[[Category:Feminine given names]]'
SURNAMES = '{{surname}}', '[[Category:Surnames]]'

RE_SECTION_TITLES = re.compile(r'^[=].*\n?', flags=re.MULTILINE)
RE_STUFF = re.compile(r'^[\|].*\n?', flags=re.MULTILINE)
RE_COMMENTS = re.compile(r'<!--.*?-->', re.DOTALL | re.UNICODE)
RE_TEMPLATE_1 = re.compile(r'{{([^}{]*)}}', re.DOTALL | re.UNICODE | re.MULTILINE)
#RE_TEMPLATE_2 = re.compile(r'{{([^}]*)}}', re.DOTALL | re.UNICODE | re.MULTILINE)
RE_NEWLINES = re.compile(r'\n+', re.DOTALL | re.UNICODE)
RE_FOOTNOTES = re.compile(r'<ref([> ].*?)(</ref>|/>)', re.DOTALL | re.UNICODE)
RE_TABLE = re.compile(r'\{\|(.*?)\|\}', re.DOTALL | re.UNICODE | re.MULTILINE)
RE_MATH = re.compile(r'<math([> ].*?)(</math>|/>)', re.DOTALL | re.UNICODE)
RE_TAGS = re.compile(r'<(.*?)>', re.DOTALL | re.UNICODE)
RE_MENTIONS = re.compile(r'\'\'\'(.*?)\'\'\'', re.DOTALL | re.UNICODE)
RE_EXTERNAL_LINKS = re.compile(r'\[(\w+):\/\/(.*?)(( (.*?))|())\]', re.UNICODE)
RE_CATEGORIES = re.compile(r'\[\[Category:(.*?)\]\]', re.UNICODE)

"""Comments."""
"""Footnotes."""
RE_P2 = re.compile(r'(\n\[\[[a-z][a-z][\w-]*:[^:\]]+\]\])+$', re.UNICODE)
"""Links to languages."""

RE_P6 = re.compile(r'\[{2}([^][]*)\|([^][]*)\]{2}', re.DOTALL | re.UNICODE)
RE_P66 = re.compile(r'\[{2}([^][]*)\]{2}', re.DOTALL | re.UNICODE)
"""Simplify links, keep description."""
RE_P16 = re.compile(r'\[{2}(.*?)\]{2}', re.UNICODE)
"""Capture interlinks text and article linked"""

RE_P9 = re.compile(r'<nowiki([> ].*?)(</nowiki>|/>)', re.DOTALL | re.UNICODE)
"""External links."""

RE_P13 = re.compile(r'(?<=(\n[ ])|(\n\n)|([ ]{2})|(.\n)|(.\t))(\||\!)([^[\]\n]*?\|)*', re.UNICODE)
"""Table cell formatting."""

RE_P17 = re.compile(
    r'(\n.{0,4}((bgcolor)|(\d{0,1}[ ]?colspan)|(rowspan)|(style=)|(class=)|(align=)|(scope=))(.*))|'
    r'(^.{0,2}((bgcolor)|(\d{0,1}[ ]?colspan)|(rowspan)|(style=)|(class=)|(align=))(.*))',
    re.UNICODE
)
RE_P18 = re.compile(r'\[{2}(.*?)\]{2}', re.UNICODE)
"""Capture interlinks text and article linked"""
"""Table markup"""

other_re = [RE_P2, RE_P9, RE_P13, RE_P17]

IGNORED_NAMESPACES = [
    'wikipedia', 'category', 'file', 'portal', 'template',
    'mediaWiki', 'user', 'help', 'book', 'draft', 'wikiProject',
    'special', 'talk', 'image','module'
]
"""MediaWiki namespaces that ought to be ignored."""

TEMPLATES_TO_KEEP = ['cvt','convert','quote','lang','wikt-lang','as of']

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


# not any(line.startswith('[[' + ignore + ':') for ignore in IGNORED_NAMESPACES)

class WikiHandler(xml.sax.ContentHandler):
    def __init__(self,outputpath, aliases,redirects,disambiguations,human_disambiguations,geo_disambiguations,number_disambiguations,
                 given_names,surnames,filename2title,title2filepath,title2Id,links,articles,stubs,link_probs):
        self.tag = ""
        self.content = ''
        self.title = ''
        self.id = -1
        self.title2Id = title2Id
        self.links = links
        self.counter_problem = 0
        self.outputpath = outputpath
        self.counter_all = 0
        self.aliases = aliases
        self.redirects = redirects
        self.disambiguations = disambiguations
        self.human_disambiguations = human_disambiguations
        self.geo_disambiguations = geo_disambiguations
        self.number_disambiguations = number_disambiguations
        self.given_names = given_names
        self.surnames = surnames
        self.attributes = {}
        self.filename2title = filename2title
        self.title2filepath = title2filepath
        self.n = 0
        self.articles = articles
        self.start = current_milli_time()
        self.stubs = stubs
        self.link_probs = link_probs

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
        elif tag == 'text':
            self.n += 1
            try:
                self.processArticle()
            except:
                print("An exception occurred for title: " + self.title)

        self.content = ""

    # Call when a character is read
    def characters(self, content):
        self.content += content

    def processArticle(self):
        text = self.content.strip()
        if text.lower().startswith('#redirect'):
            redirect = self.title
            #do nothing
        elif re.findall(RE_STUB,text.lower()):
            self.stubs.append(self.title)
            #stub article
        elif any(re.findall(RE_HUMAN_DISAMBIGUATIONS, text.lower())):
            self.human_disambiguations[self.title] = []
            filename = self.outputpath + 'disambiguations_human/' + self.title.replace(" ", '_').replace('/','_') + '.txt'
            with open(filename, 'w') as f:
                f.write(text)
            for line in text.split('\n'):
                start = line.find('[[')
                end = line.find(']]')
                if start > -1 and end > -1 and start < end:
                    entity = line[start+2:end]
                    alias = entity
                    pos_bar = entity.find('|')
                    if pos_bar > -1:
                        alias = entity[pos_bar + 1:]
                        entity = entity[:pos_bar]
                    if len(entity) > 0:
                        if entity in self.redirects:
                            entity = self.redirects[entity]
                        self.human_disambiguations[self.title].append(entity)
                        self.add_alias(entity,alias)
        elif any(re.findall(RE_GEO_DISAMBIGUATIONS, text.lower())):
            self.geo_disambiguations[self.title] = []
            filename = self.outputpath + 'disambiguations_geo/' + self.title.replace(" ", '_').replace('/','_') + '.txt'
            with open(filename, 'w') as f:
                f.write(text)
            for line in text.split('\n'):
                start = line.find('[[')
                end = line.find(']]')
                if start > -1 and end > -1 and start < end:
                    entity = line[start+2:end]
                    alias = entity
                    pos_bar = entity.find('|')
                    if pos_bar > -1:
                        alias = entity[pos_bar + 1:]
                        entity = entity[:pos_bar]
                    if len(entity) > 0:
                        if entity in self.redirects:
                            entity = self.redirects[entity]
                        self.geo_disambiguations[self.title].append(entity)
                        self.add_alias(entity,alias)
        elif any(re.findall(RE_NUMBER_DISAMBIGUATIONS, text.lower())):
            filename = self.outputpath + 'disambiguations_number/' + self.title.replace(" ", '_').replace('/','_') + '.txt'
            with open(filename, 'w') as f:
                f.write(text)
            self.number_disambiguations[self.title] = []
            for line in text.split('\n'):
                start = line.find('[[')
                end = line.find(']]')
                if start > -1 and end > -1 and start < end:
                    entity = line[start+2:end]
                    alias = entity
                    pos_bar = entity.find('|')
                    if pos_bar > -1:
                        alias = entity[pos_bar + 1:]
                        entity = entity[:pos_bar]
                    if len(entity) > 0:
                        if entity in self.redirects:
                            entity = self.redirects[entity]
                        self.number_disambiguations[self.title].append(entity)
                        self.add_alias(entity,alias)
        elif any(re.findall(RE_DISAMBIGUATIONS, text.lower())) or '(disambiguation)' in self.title:
            self.disambiguations[self.title] = []
            filename = self.outputpath + 'disambiguations_other/' + self.title.replace(" ", '_').replace('/', '_') + '.txt'
            with open(filename, 'w') as f:
                f.write(text)
            for line in text.split('\n'):
                start = line.find('[[')
                end = line.find(']]')
                if start > -1 and end > -1 and start < end:
                    entity = line[start + 2:end]
                    alias = entity
                    pos_bar = entity.find('|')
                    if pos_bar > -1:
                        alias = entity[pos_bar + 1:]
                        entity = entity[:pos_bar]
                    if len(entity) > 0:
                        if entity in self.redirects:
                            entity = self.redirects[entity]
                        self.disambiguations[self.title].append(entity)
                        self.add_alias(entity, alias)
        elif not any(self.title.lower().startswith(ignore + ':') for ignore in IGNORED_NAMESPACES):

            if any(given_name in text for given_name in GIVEN_NAMES):
                self.given_names.append(self.title)
            if '{{surname}}' in text or '[[Category:Surnames]]' in text:
                self.surnames.append(self.title)

            file_directory = re.sub('[^0-9a-z]+', '_', self.title.lower())
            while len(file_directory) < 3:
                file_directory += '_'

            if len(file_directory) > 3:
                file_directory = file_directory[:3]

            file_directory = self.outputpath + 'original_articles/' + file_directory + '/'
            
            if not os.path.isdir(file_directory):
                try:
                    mode = 0o755
                    os.mkdir(file_directory, mode)
                except FileNotFoundError:
                    print('Not found: ' + file_directory + ', name: ' + self.title)
                    file_directory = self.outputpath + 'articles/other/'
            
            relative_filename = self.title.replace(" ", '_').replace('/', '_') + '.txt'
            filename = file_directory + relative_filename
            self.filename2title[relative_filename] = self.title
            self.title2filepath[self.title] = filename
            self.articles.append(self.title)

            self.links[self.id] = {}

            pos_infobox = text.find('{{Infobox')
            if pos_infobox > -1:
                text = text[pos_infobox:]
            else:
                pos_first_linebreak = text.find('\n')
                if pos_first_linebreak > -1:
                    text = text[pos_first_linebreak:].strip()


            text = text.replace('{{snd}}',' - ')

            text, galleries = self.removeGalleries(text)
            text, other_entities = self.removeTemplates(text)

            match = re.search(RE_REMOVE_SECTIONS, text)
            if match:
                text = text[:match.span()[0]]

            text, tables = self.removeTables(text)

            for table in tables:
                other_entities.extend(self.collect_entities(table))

            text, file_descriptions = self.removeFiles(text)

            text = self.cleanText(text)
            text, mentions = self.findMentions(text)
            text = text.replace("'''", '')
            text = text.replace("''", '')
            text, links = self.removeLinks(text)

            text = re.sub(RE_P13, '', text)
            text = re.sub(RE_P2, '', text)
            text = re.sub(RE_P9, '', text)
            text = re.sub(RE_P17, '', text)

            text, actual_entities = self.fixLinks(text)
            text = text.replace('&ndash;', ' - ')
            text = text.replace('&mdash;', ' - ')
            text = text.replace('&nbsp;', ' ')

            if not self.title.lower().startswith('list of'):

                with open(filename, 'w') as f:

                    text = text.replace('&thinsp;', '')

                    lines = text.split('\n')
                    for line in lines:
                        if len(line) > 0 and line[0] == ';':
                            line = line[1:]

                        f.write(line + '\n')

                    f.write('\nACTUAL ENTITIES\n')
                    for entity in actual_entities:
                        f.write(entity + '\n')
                        if entity in self.title2Id:
                            #self.links[self.id].add(self.title2Id[entity])
                            entity_id = self.title2Id[entity]
                            if entity_id not in self.links[self.id]:
                                self.links[self.id][entity_id] = 0
                            self.links[self.id][entity_id] += 1

                    f.write('\nOTHER ENTITIES\n')
                    for entity in other_entities:
                        f.write(entity + '\n')
                        alias = entity
                        pos_bar = entity.find('|')
                        if pos_bar > -1:
                            alias = entity[pos_bar + 1:]
                            entity = entity[:pos_bar]
                        if entity in redirects:
                            entity = redirects[entity]
                        if entity in self.title2Id:
                            entity_id = self.title2Id[entity]
                            if entity_id not in self.links[self.id]:
                                self.links[self.id][entity_id] = 0
                            self.links[self.id][entity_id] += 1

                        self.add_alias(entity,alias)

        self.counter_all += 1

        if self.counter_all % 1000 == 0:
            diff = current_milli_time() - self.start
            print('Articles processed: ' + str(self.counter_all) + ', avg t: ' + str(diff / self.n), end='\r')

    def add_alias(self,entity,alias):
        if entity.lower().startswith('list of'):
            return

        if alias not in self.aliases:
            self.aliases[alias] = {}
        if entity not in self.aliases[alias]:
            self.aliases[alias][entity] = 0
        self.aliases[alias][entity] += 1

    def fixLinks(self, text):
        actual_entities = set()
        idx = 0
        while True:
            start = text[idx:].find('[[')
            if start > -1:
                end = text[idx:].find(']]')
                if end > -1:
                    if start > end:
                        idx += start
                        #print(self.title)
                        #print(start)
                        #print(end)
                        #print(idx)
                        start_print = max(0,idx + end - 100)
                        end_print = min(len(text),idx + start+100)
                        #print(text[start_print:end_print])
                    else:
                        mention = text[idx + start + 2:idx + end]
                        if mention.startswith('TEMPLATE'):
                            idx += start + 2
                        else:
                            pos_new_link = mention.find('[[')
                            if pos_new_link > -1:
                                continue_at = idx + start + 2
                                pos_bar = text[continue_at:idx+end].find('|')
                                if pos_bar > -1:
                                    continue_at += pos_bar + 1
                                text = text[:idx+start] + text[continue_at:]
                                continue
                            after = text[idx + end + 2:]
                            first_space = -1
                            for i in range(len(after)):
                                if not after[i].isalpha():
                                    first_space = i
                                    break

                            alias = mention
                            entity = mention
                            pos_bar = mention.find('|')
                            if pos_bar > -1:
                                alias = mention[pos_bar + 1:]
                                entity = mention[:pos_bar]
                            if first_space > 0:
                                alias = alias + text[idx + end + 2:idx + end + 2 + first_space]
                                end += first_space
                            if len(entity) > 0:
                                if entity in redirects:
                                    entity = redirects[entity]
                                actual_entities.add(entity)
                                self.add_alias(entity,alias)
                                before = text[:idx + start]
                                after = text[idx + end + 2:]

                                text = before + '[[' + entity + '|' + alias + ']]'

                                idx = len(text)
                                text += after
                            else:
                                text = text[:idx + start] + text[idx + start + 2:]
                else:
                    #print(self.title)
                    #print(start)
                    #print(end)
                    #print(idx)
                    start_print = max(0,idx + start - 100)
                    end_print = min(len(text),idx + start+100)
                    #print(text[start_print:end_print])
                    text = text[:idx + start] + text[idx + start + 2:]
            else:
                break

        return text,actual_entities

    def findCategories(self, text):
        categories = []

        while True:
            match = re.search(RE_CATEGORIES, text)
            if match:
                category = match.group(1)
                pos_bar = category.find('|')
                if pos_bar > -1:
                    category = category[:pos_bar]
                categories.append(category)
                text = text[:match.span()[0]] + text[match.span()[1]:]
            else:
                break

        return categories

    def removeLinks(self, text):
        links = []

        while True:
            match = re.search(RE_EXTERNAL_LINKS, text)
            if match:
                link = match.group(3)
                space = link.find(' ')
                if space > -1:
                    links.append(link[space:].strip())
                text = text[:match.span()[0]] + text[match.span()[1]:]
            else:
                break

        return text, links

    def findMentions(self, text):
        mentions = []
        text = text.strip()
        first_line_break = text.find('\n')
        if first_line_break == -1:
            first_line_break = len(text)
        while True:
            match = re.search(RE_MENTIONS, text[:first_line_break])
            if match:
                mention = match.group(1)
                if ']]' in mention and '[[' in mention:
                    text = text[:match.span()[0]] + match.group(1) + text[match.span()[1]:]
                else:
                    #text = text[:match.span()[0]] + match.group(1) + text[match.span()[1]:]
                    # text withing link
                    start = text[:match.span()[0]].rfind('[[')
                    if start > -1:
                        before = text[start:match.span()[0]]
                        if ']]' not in before:
                            end = text[match.span()[1]:].find(']]')
                            if end > -1:
                                end += match.span()[1]
                                after = text[match.span()[1]:end]
                                if '[[' not in after:
                                    text = text[:match.span()[0]] + mention + text[match.span()[1]:]
                                else:
                                    text = text[:match.span()[0]] + '###' + mention + '###' + text[match.span()[1]:]
                            else:
                                text = text[:match.span()[0]] + '###' + mention + '###' + text[match.span()[1]:]
                        else:
                            text = text[:match.span()[0]] + '###' + mention + '###' + text[match.span()[1]:]
                    else:
                        text = text[:match.span()[0]] + '###' + mention + '###' + text[match.span()[1]:]
            else:
                break
        
        text = text.replace("###","\'\'\'")
        while True:
            match = re.search(RE_MENTIONS, text[:first_line_break])
            if match:
                mention = match.group(1)
                mention = mention.replace('[[', '').replace(']]', '')
                mentions.append(mention)
                self.add_alias(self.title,mention)
                text = text[:match.span()[0]] + '[[' + self.title + '|' + mention + ']]' + text[match.span()[1]:]
            else:
                break
        return text, mentions

    def removeGalleries(self, text):
        galleries = []
        while True:
            start = text.lower().find('<gallery')
            if start > -1:
                end = text.find('</gallery>')
                if end > -1:
                    while end < start:
                        end += 10
                        end += text[end:].find('</gallery>')

                    end += 10
                    gallery = text[start:end]
                    galleries.append(gallery)
                    text = text[:start] + text[end:]
                else:
                    break
            else:
                break

        return text, galleries

    def removeTemplates(self, text):

        text = text.replace('{{spaced ndash}}', ' - ')



        while True:
            m = re.search(RE_TEMPLATE_1,text)
            if m == None:
                break

            start = m.span()[0]
            end = m.span()[1]
            template = text[start:end].lower()
            found = False
            for t in TEMPLATES_TO_KEEP:
                if template.startswith('{{' + t):
                    text = text[:start] + '{{TEMPLATE|' + m.group(1) + '}}' + text[end:]
                    found = True
                    break

            if not found:
                text = text[:start] + text[end:]

        brackets = []
        idx = 0
        while True:
            start = text[idx:].find('{{')
            if start > -1:
                start += idx
                brackets.append((start, 'opening'))
                idx = start + 2
            else:
                break

        idx = 0
        while True:
            start = text[idx:].find('}}')
            if start > -1:
                start += idx
                brackets.append((start + 2, 'closing'))
                idx = start + 2
            else:
                break

        brackets.sort(key=lambda x: x[0])

        text_to_remove = []
        counter = 0
        start_idx = -1
        end_idx = -1
        for i in range(len(brackets)):
            tuple = brackets[i]
            if tuple[1] == 'opening':
                counter += 1
                if start_idx == -1:
                    start_idx = tuple[0]
            else:
                counter -= 1
                end_idx = tuple[0]

            if counter == 0:
                if start_idx > end_idx:
                    counter += 1
                    continue

                text_to_remove.append((start_idx, end_idx))
                start_idx = -1
                end_idx = -1

        infobox_entities = []

        text_to_remove.sort(key=lambda x: x[0],reverse=True)

        offset = 0
        for i in range(len(text_to_remove)):
            tuple = text_to_remove[i]
            removed_text = text[tuple[0] - offset:tuple[1] - offset]
            if removed_text.startswith('{{Infobox') or removed_text.startswith('{{infobox'):
                infobox_entities.extend(self.collect_entities(removed_text))
            if removed_text.lower().startswith('{{template'):
                continue
            text = text[:tuple[0] - offset] + text[tuple[1] - offset:]

        return text, infobox_entities

    def collect_entities(self, text):
        entities = []

        idx = 0
        while True:
            start = text[idx:].find('[[')
            if start > -1:
                end = text[idx:].find(']]')
                if end > -1:
                    start += idx
                    end += idx

                    entity = text[start + 2:end]
                    if '[[' not in entity:
                        if not entity.lower().startswith('file:') and not entity.lower().startswith('image:') and not entity.lower().startswith('list of'):
                            entities.append(entity)




                        idx = end + 2
                    else:
                        idx = start + 2
                else:
                    break
            else:
                break

        return entities

    def removeInfobox(self, text):
        start = text.lower().find('{{infobox')
        end = -1
        open_brackets = 1
        idx = start + 2
        infobox = ''
        counter = 0
        has_problem = False
        if start > -1:
            latest = text.find('}}\n\n')
            while True:
                counter += 1
                if counter == 1000:
                    has_problem = True
                    #print(text)
                open = text[idx:].find('{{')
                close = text[idx:].find('}}')

                if close < open:
                    open_brackets -= 1
                    idx += close + 2
                else:
                    open_brackets += 1
                    idx += open + 2

                if open_brackets == 0:
                    end = idx
                    break
                elif latest < idx:
                    end = latest + 3
                    break

            infobox = text[start:end]
            return text[:start] + text[end:], infobox, has_problem
        else:
            return text, infobox, has_problem

    def removeTables(self, text):
        tables = []

        while True:
            match = re.search(RE_TABLE, text)
            if match:
                start = match.span()[0]
                end = match.span()[1]
                table = match.group(1)
                new_open = table.find('{|')
                if new_open > -1:
                    text = text[:start + new_open] + text[start + new_open + 4:end - 2] + text[end:]
                else:
                    tables.append(table)
                    text = text[:start] + text[end:]
            else:
                break

        return text, tables

    def removeFiles(self, text):
        file_descriptions = []

        while True:
            match = re.search(RE_FILES, text)
            if match:

                bracket_counter = 1
                idx = match.span()[0] + 2
                while True:
                    l = text[idx:]
                    start = text[idx:].find('[[')
                    end = text[idx:].find(']]')

                    if start > -1 and end > -1:

                        if start < end:
                            bracket_counter += 1
                            idx += start + 2
                        else:
                            bracket_counter -= 1
                            idx += end + 2

                        if bracket_counter == 0:
                            file_string = text[match.span()[0] + 3:idx - 2]

                            parts = file_string.split('|')
                            description = ''
                            if len(parts) > 1:
                                for i in range(1, len(parts)):
                                    if '[[' in parts[i]:
                                        description = '|'.join(parts[i:])
                                        break

                            if len(description) > 0:
                                description = description.replace('\n', ' ').strip()
                                file_descriptions.append(description)
                            text = text[:match.span()[0]] + text[idx:]
                            break
                    else:
                        parts = text[match.span()[0]:match.span()[1] - 3].split('|')
                        description = ''
                        if len(parts) > 1:
                            for i in range(1, len(parts)):
                                if '[[' in parts[i]:
                                    description = '|'.join(parts[i:])
                                    break

                        if len(description) > 0:
                            file_descriptions.append(description)
                        text = text[:match.span()[0]] + text[match.span()[1]:]
                        break

            else:
                break

        return text, file_descriptions

    def cleanText(self, text):
        text = re.sub(RE_COMMENTS, '', text)
        text = re.sub(RE_FOOTNOTES, '', text)
        text = re.sub(RE_MATH, '', text)
        text = re.sub(RE_TAGS, '', text)
        text = re.sub(RE_NEWLINES, '\n', text).strip()
        text = text.replace('&nbsp;', ' ')
        text = re.sub(RE_STUFF, '', text)

        return text

if (__name__ == "__main__"):
    config = json.load(open('config/config.json'))

    wikipath = config['wikipath']
    outputpath = config['outputpath']
    dictionarypath = outputpath + 'dictionaries/'
    articlepath = outputpath + 'original_articles/'

    mode = 0o755
    os.mkdir(articlepath, mode)

    os.mkdir(outputpath + 'disambiguations_human/', mode)
    os.mkdir(outputpath + 'disambiguations_number/', mode)
    os.mkdir(outputpath + 'disambiguations_geo/', mode)
    os.mkdir(outputpath + 'disambiguations_other/', mode)

    aliases = {}
    redirects = json.load(open(dictionarypath + 'redirects.json'))
    disambiguations = {}
    human_disambiguations = {}
    geo_disambiguations = {}
    number_disambiguations = {}
    title2Id = json.load(open(dictionarypath + 'title2Id.json'))
    links = {}
    link_probs = {}
    filename2title = {}
    title2filepath = {}
    given_names = []
    surnames = []
    articles = []
    stubs = []

    print('read json')

    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)
    Handler = WikiHandler(outputpath,aliases,redirects,disambiguations,human_disambiguations,geo_disambiguations,number_disambiguations,given_names,surnames,filename2title,title2filepath,title2Id,links,articles,stubs,link_probs)
    parser.setContentHandler(Handler)
    parser.parse(wikipath)
    print('done')

    with open(dictionarypath + 'aliases.json','w') as f:
        json.dump(aliases,f)
    with open(dictionarypath + 'disambiguations_other.json', 'w') as f:
        json.dump(disambiguations, f)
    with open(dictionarypath + 'disambiguations_human.json','w') as f:
        json.dump(human_disambiguations,f)
    with open(dictionarypath + 'disambiguations_geo.json','w') as f:
        json.dump(geo_disambiguations,f)
    with open(dictionarypath + 'disambiguations_number.json','w') as f:
        json.dump(number_disambiguations,f)
    with open(dictionarypath + 'given_names.json', 'w') as f:
        json.dump(given_names, f)
    with open(dictionarypath + 'surnames.json', 'w') as f:
        json.dump(surnames, f)
    with open(dictionarypath + 'filename2title.json', 'w') as f:
        json.dump(filename2title, f)
    with open(dictionarypath + 'title2filepath.json', 'w') as f:
        json.dump(title2filepath, f)
    with open(dictionarypath + 'articles.json', 'w') as f:
        json.dump(articles, f)
    with open(dictionarypath + 'links.json', 'w') as f:
        json.dump(links, f)
    with open(dictionarypath + 'stubs.json', 'w') as f:
        json.dump(links, f)
