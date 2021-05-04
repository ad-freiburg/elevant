import json
from nltk.tokenize import sent_tokenize
import re
import glob
import os
import time
from nltk.corpus import stopwords
import gender_guesser.detector as gender
import argparse

stop = set(stopwords.words('english'))

FEATURES = 12
SENTENCE_ENDS = {'.', '!', '?', ';'}
BEFORE_STRINGS = {' ', '\n', "'", '"', '}', '(', '/'}
AFTER_STRINGS = {' ', '\n', '.', ',', '?', '!', ':', ';', "'", '"', '{', ')', '/', "'s"}
POSSIBILITIES = len(BEFORE_STRINGS) * len(AFTER_STRINGS)
DATES = {'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', 'January', 'February', 'March',
         'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December', 'Jan', 'Feb', 'Mar',
         'Apr', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'}
ALPHABET = '''abcdefghijklmnopqrstuvwxyz.,<>?"'-_=+!@#$%&*(){}|1234567890'''
RE_ACRONYM = re.compile(r'\s\(([A-Z.]+)\)')
TYPE_THRESHOLD = 2

IGNORED_NAMESPACES = [
    'wikipedia', 'category', 'file', 'portal', 'template',
    'mediaWiki', 'user', 'help', 'book', 'draft', 'wikiProject',
    'special', 'talk', 'image', 'module', 'un/locode'
]


def is_number(n):
    try:
        float(n.replace('s', ''))
    except ValueError:
        return False
    return True


def is_upper(alias):
    if len(alias) > 0:
        if alias[0].isupper():
            return True
        elif alias[0].isdigit() and not is_number(alias):
            is_upper = False
            for i in range(len(alias)):
                if alias[i].isdigit() or alias[i] == ' ':
                    continue
                if alias[i].isupper():
                    is_upper = True
                    break
                elif alias[i].islower():
                    break
            return is_upper
        else:
            return False
    else:
        return False


def intersec(s1, s2):
    s1 = set(s1.split())
    s2 = set(s2.split())
    return len(s1.intersection(s2))


def add_alias(alias, article_aliases, entity, start, article_aliases_list, file_entity):
    if len(alias) > 2 and alias.endswith("'s"):
        alias = alias[:-2]

    if (alias in mostly_upper_articles and entity != file_entity) and alias != entity and (
            alias not in article_aliases or alias not in article_aliases[alias]):
        return

    if alias not in article_aliases:
        article_aliases[alias] = set()
        article_aliases_list.append(alias)
    if entity not in article_aliases[alias]:
        article_aliases[alias].add(entity)


def add_aliases(entity, article_aliases, article_aliases_list, start, file_entity):
    if entity in persons:
        tokens = entity.split()
        if len(tokens) > 1:
            tokens = [tokens[0], tokens[-1]]
        for i in range(len(tokens)):
            token = tokens[i]
            if len(token) > 1 and token[0].isupper() and (token in persons or i == len(tokens) - 1):
                if token not in article_aliases:
                    article_aliases[token] = set()
                    article_aliases_list.append(token)
                if entity not in article_aliases[token]:
                    article_aliases[token].add(entity)

    if entity in aliases_reversed:
        entity_aliases = aliases_reversed[entity]['dict']
        for alias in entity_aliases:
            if alias.lower() in stop:
                continue

            counter = entity_aliases[alias]
            if alias.startswith('the '):
                alias = alias[4:]
                if len(alias) == 0:
                    continue
            if counter > 1:
                add_alias(alias, article_aliases, entity, start, article_aliases_list, file_entity)

    if entity in redirects_reversed:
        for redirect in redirects_reversed[entity]:
            if redirect.startswith('the '):
                redirect = redirect[4:]
                if len(redirect) == 0:
                    continue

            if redirect not in article_aliases:
                article_aliases[redirect] = set()
                article_aliases_list.append(redirect)
            if entity not in article_aliases[redirect]:
                article_aliases[redirect].add(entity)

    article_aliases_list.sort(key=lambda x: len(x), reverse=True)


def add_to_unknown_persons(unknown_persons, mention):
    tokens = mention.split()
    types = {'male': 0, 'female': 0, 'unknown': 0, 'andy': 0}
    for token in tokens:
        t = gender_detector.get_gender(token)
        if t.startswith('mostly_'):
            t = t[7:]
        types[t] += 1

    if types['male'] > 0 or types['female'] > 0:
        for token in tokens:
            unknown_persons[token] = mention
        unknown_persons[mention] = mention


def find_entity_for_mention(start, mention, article_aliases, entities, all_found_aliases, file_entity, unknown_persons,
                            all_entities):
    mention_in_article_aliases = mention in article_aliases
    mention_in_human_disambiguations = mention in human_disambiguations
    mention_in_geo_disambiguations = mention in geo_disambiguations
    mention_in_given_names = False
    if mention in given_names and mention not in mostly_upper_articles:
        article_name = given_names[mention]
        if article_name in title2Id and title2Id[article_name] in links:
            mention_in_given_names = True

    mention_in_entities = False
    for e in entities:
        if e.startswith(mention):
            mention_in_entities = True
            break

    mention_in_found_aliases = False
    if mention not in mostly_upper_articles:
        for a in all_found_aliases:
            if a.startswith(mention):
                mention_in_found_aliases = True
                break

    mention_in_aliases = mention in aliases
    mention_in_redirects = mention in redirects
    mention_in_disambiguations = mention in disambiguations
    mention_in_upper = mention in mostly_upper_articles
    mention_in_popular = mention in most_popular
    mention_in_articles = mention in all_articles
    mention_in_lower = mention in mostly_lower_articles

    entity = ''
    annotation_type = 'UNKNOWN'

    if mention_in_article_aliases:
        candidates = article_aliases[mention]

        if mention in mostly_upper_articles:
            candidates.add(mention)

        new_candidates = []
        for candidate in candidates:
            if mention in candidate:
                if len(candidate) > 4 and is_number(candidate[:4]):
                    if candidate[:4] in mention:
                        new_candidates.append(candidate)
                else:
                    new_candidates.append(candidate)
            elif candidate == file_entity:
                new_candidates.append(candidate)

        if len(new_candidates) > 0:
            candidates = new_candidates

        mention_is_file_entity = mention == file_entity

        if mention_is_file_entity:
            entity = file_entity
            annotation_type = 'FILE_CANDIDATE_ARTICLE'
        else:
            all_persons = True
            file_entity_in_candidates = False
            for candidate in candidates:
                if candidate not in persons:
                    all_persons = False
                if candidate == file_entity:
                    file_entity_in_candidates = True

            mention_equals_candidate = mention in candidates
            mention_equals_candidate_or_redirect = mention in candidates or (
                    mention in redirects and redirects[mention] in candidates)
            if mention_equals_candidate and file_entity_in_candidates:
                if mention == file_entity:
                    entity = file_entity
                    annotation_type = 'FILE_ENTITY_BEST_CANDIDATE'
                else:
                    entity = file_entity + '###' + mention
                    annotation_type = 'FILE_ENTITY_AND_PERFECT_CANDIDATE'
            elif file_entity_in_candidates:
                entity = file_entity
                annotation_type = 'FILE_ENTITY_BEST_CANDIDATE'
            elif mention_equals_candidate_or_redirect:
                new_candidates = []
                for candidate in candidates:
                    if candidate == file_entity or mention in candidate or (
                            mention in redirects and redirects[mention] in candidate and mention in redirects[mention]):
                        new_candidates.append(candidate)

                if len(new_candidates) == 0:
                    new_candidates = candidates

                for candidate in new_candidates:
                    entity += '###' + candidate
                entity = entity[3:]
                annotation_type = 'MATCH_CANDIDATE_ARTICLE'
            else:
                for candidate in candidates:
                    entity += '###' + candidate
                entity = entity[3:]

                if len(candidates) == 1:
                    if mention not in all_found_aliases:
                        all_found_aliases[mention] = set([entity])
                    else:
                        all_found_aliases[mention].add(entity)
                    annotation_type = 'SINGLE_CANDIDATE_ARTICLE'
                elif all_persons and file_entity_in_candidates:
                    entity = file_entity
                    annotation_type = 'ENTITY_IN_CANDIDATES_ARTICLE'
                elif all_persons:
                    best_candidate = ''
                    most_links = 0
                    for candidate in candidates:
                        if candidate in aliases_reversed and mention in aliases_reversed[candidate]['dict'] and \
                                aliases_reversed[candidate]['dict'][mention] > most_links:
                            most_links = aliases_reversed[candidate]['dict'][mention]
                            best_candidate = candidate

                    if most_links > 0:
                        entity = best_candidate
                        annotation_type = 'BEST_PERSON_CANDIDATE_ARTICLE'
                    else:
                        annotation_type = 'MULTI_CANDIDATE_ARTICLE'
                else:
                    annotation_type = 'MULTI_CANDIDATE_ARTICLE'

    elif mention_in_human_disambiguations:
        candidates = human_disambiguations[mention]
        found = False
        for candidate in candidates:
            if candidate in entities:
                entity = candidate
                annotation_type = 'HUMAN_FOUND'
                found = True

                break

        if not found:
            annotation_type = 'HUMAN_NOTFOUND'
            entity = mention
            add_to_unknown_persons(unknown_persons, mention)

    elif mention_in_geo_disambiguations:
        candidates = geo_disambiguations[mention]
        found = False
        for candidate in candidates:
            if candidate in entities:
                annotation_type = 'GEO_FOUND'
                entity = candidate
                found = True

                break

        if not found:
            annotation_type = 'GEO_NOTFOUND'
            entity = mention

    else:
        if mention_in_given_names:
            article_name = given_names[mention]
            if article_name in title2Id and title2Id[article_name] in links:
                for e in entities:
                    if e in title2Id and title2Id[e] in links[title2Id[article_name]]:
                        entity = e
                        annotation_type = 'NAME'
                        add_to_unknown_persons(unknown_persons, mention)
                        break
        else:
            if mention_in_entities and not mention_in_upper:
                for e in entities:
                    if e.startswith(mention):
                        entity = e
                        annotation_type = 'NAME'

            elif mention_in_found_aliases:
                candidates = []
                for a in all_found_aliases:
                    if a.startswith(mention):
                        candidates.extend(list(all_found_aliases[a]))

                entity = ''
                for candidate in candidates:
                    entity += '###' + candidate
                entity = entity[3:]

                if len(candidates) == 1:
                    annotation_type = 'SINGLE_IN_ALIAS'
                else:
                    annotation_type = 'MULTI_IN_ALIAS'

            elif (mention_in_aliases and len(aliases[mention]['dict']) > 0) or mention_in_redirects:
                if mention_in_redirects and (
                        redirects[mention] in mostly_upper_articles or not redirects[mention] in mostly_lower_articles):
                    annotation_type = 'REDIRECT'
                    entity = redirects[mention]
                    all_entities.add(redirects[mention])

                elif mention_in_disambiguations and not mention_in_redirects and not mention_in_upper:
                    candidates = disambiguations[mention]

                    actual_candidates = []
                    for candidate in candidates:
                        if candidate in entities or candidate in all_entities:
                            actual_candidates.append(candidate)

                    if len(actual_candidates) == 1:
                        annotation_type = 'DISAMBIGUATION_CAND'
                        entity = actual_candidates[0]
                    else:
                        annotation_type = 'DISAMBIGUATION_' + str(len(actual_candidates))
                        entity = mention

                elif (mention_in_redirects or mention_in_articles) and not mention_in_upper:
                    entity = ''
                    annotation_type = 'UNKNOWN'
                elif mention_in_upper and mention_in_popular:
                    entity = mention
                    annotation_type = 'UPPER_ENTITY'
                elif start > 0:
                    candidates = aliases[mention]['list']
                    entity = candidates[0][0]
                    if len(candidates) == 1:
                        annotation_type = 'UPPER_ENTITY'
                    else:
                        annotation_type = 'MULTI_CANDIDATE_ALIASES'

    if annotation_type == 'UNKNOWN' and mention in unknown_persons:
        entity = unknown_persons[mention]
        annotation_type = 'UNKNOWN_PERSON'

    return entity, annotation_type


def annotate_entities(sentence, article_aliases, article_aliases_list, sentence_starters, start_of_sentence, entities,
                      all_found_aliases, file_entity, all_entities, unknown_persons):
    found_entities = []
    end_of_sentence = ''
    if len(sentence) == 0:
        return sentence

    if sentence[-1] in SENTENCE_ENDS:
        end_of_sentence = sentence[-1]
        sentence = sentence[:-1]

    found_acronym = False
    for m in re.finditer(RE_ACRONYM, sentence):
        acronym = m.group(1).replace('.', '')
        before = sentence[:m.span(0)[0]]

        if len(before) == 0 or len(acronym) == 0:
            continue

        uppercase_letters = []
        uppercase_letters_string = ''
        for i in range(len(before)):
            c = before[i]
            if c.isupper():
                uppercase_letters.append(i)
                uppercase_letters_string += c

        if len(uppercase_letters) >= len(acronym) and uppercase_letters_string[-len(acronym):] == acronym:
            start_idx = uppercase_letters[-len(acronym)]
            actual_entity = before[start_idx:]

            placeholder = ''
            for i in range(len(actual_entity)):
                placeholder += '#'

            entity, annotation_type = find_entity_for_mention(uppercase_letters[-len(acronym)], actual_entity,
                                                              article_aliases, entities, all_found_aliases,
                                                              file_entity, unknown_persons, all_entities)

            if len(entity) == 0:
                entity = actual_entity
            found_entities.append(
                (uppercase_letters[-len(acronym)], len(actual_entity), entity, annotation_type, actual_entity))
            sentence = sentence[:uppercase_letters[-len(acronym)]] + placeholder + sentence[uppercase_letters[
                                                                                                -len(acronym)] + len(
                actual_entity):]

            placeholder = ''
            for i in range(len(acronym)):
                placeholder += '#'

            found_entities.append((m.span(1)[0], len(acronym), entity, acronym))
            sentence = sentence[:m.span(1)[0]] + placeholder + sentence[m.span(1)[0] + len(acronym):]

    for alias in article_aliases_list:
        while True:
            pos_alias = sentence.find(alias)
            if pos_alias > -1:
                before = sentence[:pos_alias]
                after = sentence[pos_alias + len(alias):]
                before_string = None
                after_string = None
                if pos_alias > 0 and before[-1] in BEFORE_STRINGS:
                    before_string = before[-1]
                elif pos_alias > 1 and before[-2:] in BEFORE_STRINGS:
                    before_string = before[-2:]
                elif pos_alias == 0:
                    before_string = ''

                len_after = len(after)
                if len_after > 0 and after[0] in AFTER_STRINGS:
                    after_string = after[0]
                elif len_after > 1 and after[:2] in AFTER_STRINGS:
                    after_string = after[:2]
                elif len_after == 0:
                    after_string = ''

                if before_string is None or after_string is None:
                    break
                else:
                    string_to_match = before_string + alias + after_string
                    pos_alias = pos_alias - len(before_string)
                    placeholder = ''
                    for i in range(len(alias)):
                        placeholder += '#'

                    found_entities.append((pos_alias + len(before_string), len(alias), alias))
                    sentence = sentence[:pos_alias + len(before_string)] + placeholder + sentence[pos_alias + len(
                        string_to_match) - len(after_string):]
            else:
                break

    sentence_temp = "".join([c if c.isalnum() or c == '-' else " " for c in sentence])
    tokens = sentence_temp.split(' ')
    previous = ''
    first_word_index = -1
    for j in range(len(tokens)):
        token = tokens[j]
        if len(token) > 0 and first_word_index == -1:
            first_word_index = j
        if len(token) > 0 and token[0].isupper() and not is_number(token):
            is_start_of_new_sentence = (j == first_word_index and start_of_sentence) or sentence[len(previous) - 2:len(
                previous)] == ': '
            next_word_upper = len(tokens) > j + 1 and len(tokens[j + 1]) > 0 and tokens[j + 1][0].isupper()
            if is_start_of_new_sentence and token.lower() in stop:
                previous += ' ' + token
                continue
            if token in DATES:
                previous += ' ' + token
                continue
            if token not in unknown_persons and is_start_of_new_sentence and not next_word_upper and (
                    token.lower() in sentence_starters or token not in article_aliases) and token not in mostly_upper_articles:
                previous += ' ' + token
                continue

            if len(token) == 1 and len(sentence) > len(previous) + len(token) and sentence[
                len(previous) + len(token)] == '.':
                found_entities.append((len(previous), len(token) + 1))  # This can be part of a middle name
            else:
                found_entities.append((len(previous), len(token)))  # Found upper case entity
        previous += ' ' + token

    found_entities.sort(key=lambda x: x[0], reverse=False)

    # Replace placeholders with actual mention
    for found_entity in found_entities:
        if len(found_entity) > 2:
            sentence = sentence[:found_entity[0]] + found_entity[-1] + sentence[found_entity[0] + found_entity[1]:]

    j = 0
    while j < len(found_entities) - 1:
        if found_entities[j][0] == -1:
            j += 1
            continue

        next = -1
        for k in range(j + 1, len(found_entities)):
            if found_entities[k][0] != -1:
                next = k
                break

        if next == -1:
            break
        first_mention = sentence[found_entities[j][0]: found_entities[j][0] + found_entities[j][1]]
        second_mention = sentence[found_entities[next][0]: found_entities[next][0] + found_entities[next][1]]
        between = sentence[found_entities[j][0] + found_entities[j][1]:found_entities[next][0]]

        mention = first_mention + between + second_mention

        mention_in_article_aliases = mention in article_aliases
        mention_in_human_disambiguations = mention in human_disambiguations
        mention_in_geo_disambiguations = mention in geo_disambiguations
        mention_in_given_names = mention in given_names
        mention_in_entities = False
        for e in entities:
            if e.startswith(mention):
                mention_in_entities = True
                break
        mention_in_aliases = mention in aliases and len(set(aliases[mention]['dict']).intersection(all_entities)) > 0
        mention_in_aliases_reversed = mention in aliases_reversed
        mention_in_redirects = mention in redirects
        mention_in_disambiguations = mention in disambiguations
        mention_in_upper = mention in mostly_upper_articles
        mention_in_articles = mention in all_articles

        if len(between) == 0 or between == ' ' or between == ' & ' or between == '-' or re.sub(r'\W+', '',
                                                                                               between).strip() in {
            'de', 'of', 'von',
            'van'} or mention_in_article_aliases or mention_in_aliases or mention_in_redirects or mention_in_aliases_reversed:
            found_entities[j] = (found_entities[j][0], len(mention))
            found_entities[next] = (-1, -1)
            j -= 1
        j += 1

    found_entities.sort(key=lambda x: x[0], reverse=True)

    for j in range(len(found_entities)):
        if found_entities[j][0] == -1:
            continue

        start = found_entities[j][0]
        length = found_entities[j][1]
        mention = sentence[start: start + length]

        if mention == 'I' or is_number(mention.replace('.', '').replace('s', '')):
            continue

        if len(found_entities[j]) == 5:
            entity = '[[' + found_entities[j][2] + '|' + mention + '|' + found_entities[j][3] + ']]'
        elif len(found_entities[j]) == 4:
            entity = '[[' + found_entities[j][2] + '|' + mention + '|ACRONYM]]'
        else:
            entity, annotation_type = find_entity_for_mention(start, mention, article_aliases, entities,
                                                              all_found_aliases, file_entity, unknown_persons,
                                                              all_entities)

            if 'UNKNOWN' == annotation_type and mention.lower() in stop:
                entity = None

            if 'UNKNOWN' == annotation_type:
                add_to_unknown_persons(unknown_persons, mention)

            if entity == None:
                entity = mention
            else:
                if len(entity) == 0:
                    entity = mention
                entity = '[[' + entity + '|' + mention + '|' + annotation_type + ']]'

        sentence = sentence[:start] + entity + sentence[start + length:]

    sentence = sentence + end_of_sentence
    return sentence


def combine_entities(content):
    content = re.sub(' +', ' ', content)
    idx = 0
    while True:
        pos = content[idx:].find(']] [[')
        if pos > -1:
            pos += idx
            start = content[:pos].rfind('[[')
            end = content[pos + 5:].find(']]')
            if start > -1 and end > -1:
                end += pos + 5
                all = content[start + 2:end]
                if all.count('ANNOTATION') == 1:
                    first_part_tokens = content[start + 2:pos].split('|')
                    second_part_tokens = content[pos + 5:end].split('|')
                    alias = first_part_tokens[-2] + ' ' + second_part_tokens[-2]
                    if 'ANNOTATION' in first_part_tokens[-1]:
                        annotation = first_part_tokens[-1]
                        entity = first_part_tokens[0]
                    else:
                        annotation = second_part_tokens[-1]
                        entity = second_part_tokens[0]

                    content = content[:start] + '[[' + entity + '|' + alias + '|' + annotation + ']]' + content[
                                                                                                        end + 2:]
                    idx = start + len(entity) + len(alias) + len(annotation) + 6
                else:
                    idx = pos + 5
            else:
                break
        else:
            break

    return content


def break_content(content, file_entity):
    lines = content.split('\n')
    sentences = []

    STARTERS = ['.', ',', '*', '?', '!', '@', '#', '$', '%', '^', '&']

    for line in lines:
        line = line.strip()

        if line.startswith('[[Category:'):
            continue

        # print('start line loop')
        while len(line) > 0 and any(line[0] == s for s in STARTERS):
            line = line[1:]
            line = line.strip()

        if len(line) == 0:
            continue

        sent_tokenize_list = sent_tokenize(line.strip())
        new_sent_tokenize_list = []
        i = 0
        while i < len(sent_tokenize_list):
            if i > 0 and len(sent_tokenize_list[i]) > 0 and sent_tokenize_list[i].lstrip()[0].isalpha() and \
                    sent_tokenize_list[i].lstrip()[0].islower():
                sent_tokenize_list[i - 1] = sent_tokenize_list[i - 1] + ' ' + sent_tokenize_list[i]
                sent_tokenize_list[i] = ''
            i += 1

        current_sentences = []
        i = 0
        previously_added = -1
        while i < len(sent_tokenize_list):
            starts = sent_tokenize_list[i].count('[[')
            ends = sent_tokenize_list[i].count(']]')
            if starts != ends:
                next = -1
                for j in range(i + 1, len(sent_tokenize_list)):
                    if len(sent_tokenize_list[j]) > 0:
                        next = j
                        break

                if next > -1:
                    sent_tokenize_list[i] += sent_tokenize_list[next]

                    sent_tokenize_list[next] = ''
                    i -= 1
            if len(sent_tokenize_list[i]) > 0 and i != previously_added:
                previously_added = i
                if sent_tokenize_list[i] in file_entity and len(file_entity) > len(sent_tokenize_list[i]) and i < len(
                        sent_tokenize_list) - 1:
                    sent_tokenize_list[i + 1] = sent_tokenize_list[i] + sent_tokenize_list[i + 1]
                else:
                    current_sentences.append(sent_tokenize_list[i])
            i += 1
        sentences.append(current_sentences)

    return sentences


def find_entities(content, entities, all_entities):
    pos_actual = content.find('ACTUAL ENTITIES')
    pos_other = content.find('OTHER ENTITIES')
    actual_entity_content = content[pos_actual + 15:pos_other]
    other_entity_content = content[pos_other + 14:]

    for line in actual_entity_content.split('\n'):
        line = line.strip()
        mention = line
        pos_bar = mention.find('|')
        if pos_bar > -1:
            entity = mention[:pos_bar]
        else:
            entity = mention
        if entity in redirects:
            entity = redirects[entity]
        all_entities.add(entity)

    for line in other_entity_content.split('\n'):
        line = line.strip()
        mention = line
        pos_bar = mention.find('|')
        if pos_bar > -1:
            entity = mention[:pos_bar]
        else:
            entity = mention
        if entity in redirects:
            entity = redirects[entity]
        entities.add(entity)
        all_entities.add(entity)

    return content[:pos_actual]


def process_file(filepath, output_filename, benchmark):
    filename = filepath.split('/')[-1]
    if benchmark:
        filename = filename[len("article_00000_"):]
    with open(filepath, "r", encoding="utf8") as f:
        if filename in filename2title:
            file_entity = filename2title[filename]
        else:
            file_entity = filename[:-4].replace('_', ' ')

        if file_entity in mostly_lower_articles:
            return

        entities = set()
        unknown_persons = {}
        all_entities = set()
        all_found_aliases = {}
        article_aliases = {}
        article_aliases_list = []
        complete_content = ''

        first_name = None
        if file_entity in persons:
            first_name = file_entity.split(' ')[0]

        file_content = f.read()
        file_content = find_entities(file_content, entities, all_entities)
        sent_tokenize_list = break_content(file_content, file_entity)

        for lines in sent_tokenize_list:
            for content in lines:
                content = content.strip()
                if any(content.lower().startswith('[[' + ignore + ':') for ignore in IGNORED_NAMESPACES):
                    continue
                if content.startswith('='):
                    complete_content += '\n' + content
                    continue
                if len(content) == 0 or (content.startswith('*') and len(content[1:].strip()) == 0):
                    continue

                idx = 0
                start_of_sentence = True
                while True:
                    start = content[idx:].find('[[')
                    end = content[idx:].find(']]')

                    # if start > -1 or end > -1:
                    #    if start > end or (start > -1 and end == -1) or (start == -1 and end > -1):
                    #        print(file_entity)
                    #        print(content)

                    if start > -1 and end > -1 and end > start:
                        start += idx
                        end += idx
                        previous_part = content[idx:start]

                        previous_part = annotate_entities(previous_part, article_aliases, article_aliases_list,
                                                          sentence_starters, start_of_sentence, entities,
                                                          all_found_aliases, file_entity, all_entities, unknown_persons)
                        start_of_sentence = False

                        mention = content[start + 2:end]

                        if 'TEMPLATE' in mention:
                            first_part = content[:idx] + previous_part + '[[' + mention + ']]'
                            idx = len(first_part)
                            content = first_part + content[end + 2:]
                        else:
                            pos_bar = mention.find('|')
                            alias = mention[pos_bar + 1:]
                            entity = mention[:pos_bar]

                            if entity in redirects:
                                entity = redirects[entity]

                            if entity in redirects:
                                entity = redirects[entity]

                            if entity in mostly_upper_articles and is_upper(alias):
                                add_aliases(entity, article_aliases, article_aliases_list, end + 2, file_entity)

                                if entity not in aliases_reversed:
                                    first_part = content[
                                                 :idx] + previous_part + '[[' + entity + '|' + alias + '|NOENTITY_ANNOTATION]]'
                                elif alias not in aliases_reversed[entity]['dict'] or aliases_reversed[entity]['dict'][
                                    alias] <= 1:
                                    first_part = content[
                                                 :idx] + previous_part + '[[' + entity + '|' + alias + '|RARE_ANNOTATION]]'
                                else:
                                    first_part = content[
                                                 :idx] + previous_part + '[[' + entity + '|' + alias + '|ANNOTATION]]'

                                idx = len(first_part)
                                content = first_part + content[end + 2:]

                                if alias not in all_found_aliases:
                                    all_found_aliases[alias] = set([entity])
                                else:
                                    es = all_found_aliases[alias]
                                    all_found_aliases[alias].add(entity)

                                es = all_found_aliases[alias]

                                entities.add(entity)
                            else:
                                alias = annotate_entities(alias, article_aliases, article_aliases_list,
                                                          sentence_starters, start_of_sentence, entities,
                                                          all_found_aliases, file_entity, all_entities, unknown_persons)

                                first_part = content[:idx] + previous_part + alias

                                idx = len(first_part)
                                content = first_part + content[end + 2:]
                    else:
                        break

                sentence = content[idx:]

                sentence = annotate_entities(sentence, article_aliases, article_aliases_list, sentence_starters,
                                             start_of_sentence, entities, all_found_aliases, file_entity, all_entities,
                                             unknown_persons)
                content = content[:idx] + sentence

                content = combine_entities(content)
                complete_content += '\n' + content
                complete_content = complete_content.strip()

            complete_content += '\n'

        complete_content = complete_content.strip()
        if len(complete_content) > 0:
            with open(output_filename, 'w', encoding="utf8") as f:
                complete_content = complete_content.replace('()', '')
                complete_content = re.sub(' +', ' ', complete_content)
                f.write(complete_content)


def process(article, file_directory, benchmark):
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
        original_articlepath = outputpath + 'fixed_link_articles_benchmark/'
        processed_articlepath = outputpath + 'processed_articles_benchmark/'
    else:
        original_articlepath = outputpath + 'original_articles/'
        processed_articlepath = outputpath + 'processed_articles/'

    mode = 0o755

    if not os.path.isdir(processed_articlepath):
        try:
            os.mkdir(processed_articlepath, mode)
        except FileNotFoundError:
            print('Not found: ' + processed_articlepath)
            exit(1)

    print("Loading dictionaries...")
    persons = set(json.load(open('data/persons.json')))
    sentence_starters = set(json.load(open('data/frequent_sentence_starters.json')))

    aliases_reversed = json.load(open(dictionarypath + 'aliases_reversed_sorted_pruned_upper.json'))
    aliases = json.load(open(dictionarypath + 'aliases_sorted_pruned_upper.json'))
    redirects_reversed = json.load(open(dictionarypath + 'redirects_reversed_upper.json'))
    mostly_upper_articles = set(json.load(open(dictionarypath + 'mostly_upper.json')))
    mostly_lower_articles = set(json.load(open(dictionarypath + 'mostly_lower.json')))
    redirects = json.load(open(dictionarypath + 'redirects.json'))
    all_articles = set(json.load(open(dictionarypath + 'articles.json')))
    disambiguations = json.load(open(dictionarypath + 'disambiguations_other.json'))
    human_disambiguations = json.load(open(dictionarypath + 'disambiguations_human.json'))
    geo_disambiguations = json.load(open(dictionarypath + 'disambiguations_geo.json'))
    given_names = json.load(open(dictionarypath + 'given_names_dict.json'))
    filename2title = json.load(open(dictionarypath + 'filename2title.json'))
    links = json.load(open(dictionarypath + 'links.json'))
    title2Id = json.load(open(dictionarypath + 'title2Id.json'))
    most_popular = json.load(open(dictionarypath + 'most_popular_entities_10000.json'))
    gender_detector = gender.Detector()

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
            process(article, file_directory, args.benchmark)

        end = time.time()
        diff_acc += end - start
        c += len(articles)
        avg = (diff_acc / c) * 1000
        print(str(c) + ', avg t: ' + str(avg), end='\r')
    print()
    print("Wrote processed articles to %s" % processed_articlepath)
