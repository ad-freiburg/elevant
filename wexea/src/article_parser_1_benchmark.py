import argparse
import re
import os
import json
import glob
import time

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
# RE_TEMPLATE_2 = re.compile(r'{{([^}]*)}}', re.DOTALL | re.UNICODE | re.MULTILINE)
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
    'special', 'talk', 'image', 'module'
]
"""MediaWiki namespaces that ought to be ignored."""

TEMPLATES_TO_KEEP = ['cvt', 'convert', 'quote', 'lang', 'wikt-lang', 'as of']


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


# not any(line.startswith('[[' + ignore + ':') for ignore in IGNORED_NAMESPACES)

def processArticle(input_file, output_file):
    text = ''.join(open(input_file, "r", encoding="utf8").readlines())
    """
    self.articles.append(self.title)

    self.links[self.id] = {}

    pos_infobox = text.find('{{Infobox')
    if pos_infobox > -1:
        text = text[pos_infobox:]
    else:
        pos_first_linebreak = text.find('\n')
        if pos_first_linebreak > -1:
            text = text[pos_first_linebreak:].strip()

    text = text.replace('{{snd}}', ' - ')

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
    """
    text, actual_entities = fixLinks(text)
    text = text.replace('&ndash;', ' - ')
    text = text.replace('&mdash;', ' - ')
    text = text.replace('&nbsp;', ' ')

    with open(output_file, 'w', encoding="utf8") as f:

        text = text.replace('&thinsp;', '')

        lines = text.split('\n')
        for line in lines:
            if len(line) > 0 and line[0] == ';':
                line = line[1:]

            f.write(line + '\n')

        f.write('\nACTUAL ENTITIES\n')
        for entity in actual_entities:
            f.write(entity + '\n')

        f.write('\nOTHER ENTITIES\n')


def fixLinks(text):
    actual_entities = set()
    idx = 0
    while True:
        start = text[idx:].find('[[')
        if start > -1:
            end = text[idx:].find(']]')
            if end > -1:
                if start > end:
                    idx += start
                    # print(self.title)
                    # print(start)
                    # print(end)
                    # print(idx)
                    start_print = max(0, idx + end - 100)
                    end_print = min(len(text), idx + start + 100)
                    # print(text[start_print:end_print])
                else:
                    mention = text[idx + start + 2:idx + end]
                    if mention.startswith('TEMPLATE'):
                        idx += start + 2
                    else:
                        pos_new_link = mention.find('[[')
                        if pos_new_link > -1:
                            continue_at = idx + start + 2
                            pos_bar = text[continue_at:idx + end].find('|')
                            if pos_bar > -1:
                                continue_at += pos_bar + 1
                            text = text[:idx + start] + text[continue_at:]
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
                            before = text[:idx + start]
                            after = text[idx + end + 2:]

                            text = before + '[[' + entity + '|' + alias + ']]'

                            idx = len(text)
                            text += after
                        else:
                            text = text[:idx + start] + text[idx + start + 2:]
            else:
                # print(self.title)
                # print(start)
                # print(end)
                # print(idx)
                start_print = max(0, idx + start - 100)
                end_print = min(len(text), idx + start + 100)
                # print(text[start_print:end_print])
                text = text[:idx + start] + text[idx + start + 2:]
        else:
            break

    return text, actual_entities


if __name__ == "__main__":
    def process(article, file_directory):
        output_filename = file_directory + article.split('/')[-1]
        processArticle(article, output_filename)


    if __name__ == "__main__":
        parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description=__doc__)

        parser.add_argument("--only_new", action="store_true",
                            help="Process only articles in the article directory \"new\".")

        args = parser.parse_args()

        config = json.load(open('config/config.json'))

        outputpath = config['outputpath']

        original_articlepath = outputpath + 'original_articles_benchmark/'
        processed_articlepath = outputpath + 'fixed_link_articles_benchmark/'

        dictionarypath = outputpath + 'dictionaries/'
        redirects = json.load(open(dictionarypath + 'redirects.json'))

        mode = 0o755

        if not os.path.isdir(processed_articlepath):
            try:
                os.mkdir(processed_articlepath, mode)
            except FileNotFoundError:
                print('Not found: ' + processed_articlepath)
                exit(1)

        article_directories = glob.glob(original_articlepath + "*/")

        diff_acc = 0.0
        c = 0
        print("Processing articles at %s ..." % original_articlepath)
        for article_directory in article_directories:
            folder_name = article_directory.split('/')[-2]

            if args.only_new and folder_name != "new":
                continue

            articles = glob.glob(article_directory + "*.txt")

            file_directory = processed_articlepath + folder_name + '/'

            if not os.path.isdir(file_directory):
                try:
                    mode = 0o755
                    os.mkdir(file_directory, mode)
                except FileNotFoundError:
                    print('Not found: ' + file_directory)
                    exit(1)

            start = time.time()

            for article in articles:
                process(article, file_directory)

            end = time.time()
            diff_acc += end - start
            c += len(articles)
            avg = (diff_acc / c) * 1000
            print(str(c) + ', avg t: ' + str(avg), end='\r')
        print()
        print("Wrote processed articles to %s" % processed_articlepath)