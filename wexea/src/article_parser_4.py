import argparse
import glob
import json
import os
import re
import time
import gender_guesser.detector as gender

def annotate_previous_part(previous_part, all_corefs):
    found_corefs = []

    original_previous_part = previous_part

    for coref in all_corefs:
        if all_corefs[coref] == None:
            continue
        regex = r"\b" + re.escape(coref) + r"\b"
        placeholder = ''
        for i in range(len(coref)):
            placeholder += '#'
        starts = [(m.start(), coref, all_corefs[coref]) for m in re.finditer(regex, previous_part.lower())]
        found_corefs.extend(starts)
        for start in starts:
            previous_part = previous_part[:start[0]] + placeholder + previous_part[start[0] + len(placeholder):]

    found_corefs.sort(key=lambda x: x[0], reverse=True)
    for found_coref in found_corefs:
        start = found_coref[0]
        coref = original_previous_part[start:start + len(found_coref[1])]
        entity = found_coref[2]
        previous_part = previous_part[:start] + '[[' + entity + '|' + coref + '|COREF]]' + previous_part[start + len(coref):]

    return previous_part, len(found_corefs)


def process_file(filepath, output_filename, benchmark):
    filename = filepath.split('/')[-1]
    if benchmark:
        filename = filename[len("article_00000_"):]
    with open(filepath, "r", encoding="utf8") as f:
        all_corefs = {}

        if filename in filename2title:
            file_entity = filename2title[filename]
        else:
            file_entity = filename[:-4].replace('_', ' ')

        if file_entity in mostly_lower_articles:
            return

        with open(output_filename, 'w', encoding="utf8") as f_out:

            file_entity_gender = None
            if file_entity in person_corefs:
                if person_corefs[file_entity] == 'he':
                    file_entity_gender = 'male'
                else:
                    file_entity_gender = 'female'

            if file_entity in corefs:
                file_entity_corefs = corefs[file_entity]
                for coref in file_entity_corefs:
                    all_corefs[coref] = file_entity

            all_corefs['his'] = None
            all_corefs['him'] = None
            all_corefs['he'] = None
            all_corefs['her'] = None
            all_corefs['she'] = None
            if file_entity_gender == 'male':
                all_corefs['his'] = file_entity
                all_corefs['him'] = file_entity
                all_corefs['he'] = file_entity
            elif file_entity_gender == 'female':
                all_corefs['her'] = file_entity
                all_corefs['she'] = file_entity

            for line in f:
                content = line.strip()
                if '[[[[' in content or ']]]]' in content:
                    continue
                if len(content) == 0:
                    all_corefs['his'] = None
                    all_corefs['him'] = None
                    all_corefs['he'] = None
                    all_corefs['her'] = None
                    all_corefs['she'] = None
                    if file_entity_gender == 'male':
                        all_corefs['his'] = file_entity
                        all_corefs['him'] = file_entity
                        all_corefs['he'] = file_entity
                    elif file_entity_gender == 'female':
                        all_corefs['her'] = file_entity
                        all_corefs['she'] = file_entity
                    #f_out.write('\n')
                else:
                    idx = 0
                    while True:
                        start = content[idx:].find('[[')
                        end = content[idx:].find(']]')

                        if end < start:
                            end = content[idx+start:].find(']]')
                            if end > -1:
                                end += start

                        if start > -1 and end > -1 and end > start:
                            start += idx
                            end += idx
                            previous_part = content[idx:start]
                            previous_part, len_found_corefs = annotate_previous_part(previous_part, all_corefs)

                            if len_found_corefs > 0:
                                content = content[:idx] + previous_part + content[start:]
                                continue

                            mention = content[start + 2:end]
                            if 'TEMPLATE' in mention:
                                content = content[:start] + content[end + 2:].strip()
                                idx = start
                            else:
                                tokens = mention.split('|')
                                if len(tokens) == 3:
                                    alias = tokens[1]
                                    entity = tokens[0]
                                    annotation_type = tokens[2]
                                elif len(tokens) == 2:
                                    alias = tokens[0]
                                    entity = alias
                                    annotation_type = tokens[1]
                                elif len(tokens) > 3:
                                    entity = tokens[0]
                                    alias = tokens[0]
                                    annotation_type = 'PROBLEM'
                                else:
                                    entity = 'UNKNOWN'

                                if entity in person_corefs:
                                    if person_corefs[entity] == 'he':
                                        all_corefs['his'] = entity
                                        all_corefs['him'] = entity
                                        all_corefs['he'] = entity
                                    else:
                                        all_corefs['her'] = entity
                                        all_corefs['she'] = entity
                                elif entity not in corefs and 'disambiguation' not in entity:
                                    tokens = entity.split(' ')
                                    types = {'male':0,'female':0,'unknown':0,'andy':0}
                                    for token in tokens:
                                        t = gender_detector.get_gender(token)
                                        if t.startswith('mostly_'):
                                            t = t[7:]
                                        types[t] += 1

                                    if types['male'] > 0 and types['female'] == 0:
                                        all_corefs['his'] = entity
                                        all_corefs['him'] = entity
                                        all_corefs['he'] = entity
                                    elif types['male'] == 0 and types['female'] > 0:
                                        all_corefs['her'] = entity
                                        all_corefs['she'] = entity

                                idx = end + 2

                                if entity in corefs:
                                    l = corefs[entity]
                                    for coref in l:
                                        all_corefs[coref] = entity
                        else:
                            previous_part, len_found_corefs = annotate_previous_part(content[idx:], all_corefs)
                            if len_found_corefs > 0:
                                content = content[:idx] + previous_part
                                continue

                            break

                    f_out.write(content.strip() + '\n')

def process(article,file_directory, benchmark):
    output_filename = file_directory + article.split('/')[-1]
    process_file(article, output_filename, benchmark)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("--benchmark", action="store_true",
                        help="Link benchmark articles instead of entire Wikipedia dump.")
    parser.add_argument("--only_new", action="store_true",
                        help="Process only articles in the article directory \"new\".")

    args = parser.parse_args()

    config = json.load(open('config/config.json'))

    outputpath = config['outputpath']
    dictionarypath = outputpath + 'dictionaries/'
    if args.benchmark:
        el_articlepath = outputpath + 'el_articles_benchmark/'
        final_articlepath = outputpath + 'almost_final_articles_benchmark/'
    else:
        el_articlepath = outputpath + 'el_articles/'
        final_articlepath = outputpath + 'final_articles/'

    if not os.path.isdir(final_articlepath):
        try:
            mode = 0o755
            os.mkdir(final_articlepath, mode)
        except FileNotFoundError:
            print('Not found: ' + final_articlepath)
            exit(1)

    print('Loading dictionaries...')
    filename2title = json.load(open(dictionarypath + 'filename2title.json'))
    corefs = json.load(open('data/corefs.json'))
    mostly_lower_articles = set(json.load(open(dictionarypath + 'mostly_lower.json')))
    gender_detector = gender.Detector()

    person_corefs = {}
    new_corefs = {}
    for entity in corefs:
        l = corefs[entity]
        new_l = []
        for c in l:
            if c == ' he ':
                person_corefs[entity] = 'he'
            elif c == ' she ':
                person_corefs[entity] = 'she'
            else:
                new_l.append(c.strip())

        if len(new_l) > 0:
            new_corefs[entity] = new_l

    corefs = new_corefs

    article_directories = glob.glob(el_articlepath + "*/")

    print("Processing articles at %s ..." % el_articlepath)
    diff_acc = 0.0
    c = 0
    for article_directory in article_directories:
        folder_name = article_directory.split('/')[-2]

        if args.only_new and folder_name != "new":
            continue

        articles = glob.glob(article_directory + "*.txt")

        file_directory = final_articlepath + folder_name + '/'

        if not os.path.isdir(file_directory):
            try:
                mode = 0o755
                os.mkdir(file_directory, mode)
            except FileNotFoundError:
                print('Not found: ' + file_directory)
                exit(1)

        start = time.time()

        for article in articles:
            process(article, file_directory, args.benchmark)

        end = time.time()
        diff_acc += end - start
        c += len(articles)
        avg = (diff_acc / c) * 1000
        print(str(c) + ', avg t: ' + str(avg), end='\r')
    print("Wrote processed articles to %s" % final_articlepath)
