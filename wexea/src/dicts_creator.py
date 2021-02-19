import json
import os
from nltk.corpus import stopwords
stop = set(stopwords.words('english'))

IGNORED_NAMESPACES = [
    'wikipedia', 'category', 'file', 'portal', 'template',
    'mediaWiki', 'user', 'help', 'book', 'draft', 'wikiProject',
    'special', 'talk', 'image','module','un/locode'
]

def is_number(n):
    try:
        float(n)
    except ValueError:
        return False
    return True


config = json.load(open('config/config.json'))

outputpath = config['outputpath']
dictionarypath = outputpath + 'dictionaries/'
original_articlepath = outputpath + 'original_articles/'
processed_articlepath = outputpath + 'processed_articles/'

articles = set(json.load(open(dictionarypath + 'articles.json')))
redirects = json.load(open(dictionarypath + 'redirects.json'))
aliases = json.load(open(dictionarypath + 'aliases.json'))
given_names = json.load(open(dictionarypath + 'given_names.json'))
surnames = json.load(open(dictionarypath + 'surnames.json'))
other_disambiguations = json.load(open(dictionarypath + 'disambiguations_other.json'))
human_disambiguations = json.load(open(dictionarypath + 'disambiguations_human.json'))
geo_disambiguations = json.load(open(dictionarypath + 'disambiguations_geo.json'))
number_disambiguations = json.load(open(dictionarypath + 'disambiguations_number.json'))
disambiguation_dicts = [other_disambiguations,human_disambiguations,geo_disambiguations,number_disambiguations]

given_names_dict = {}
for given_name in given_names:
    idx = given_name.find('(')
    if idx > -1:
        actual_name = given_name[:idx].strip()
    else:
        actual_name = given_name

    given_names_dict[actual_name] = given_name

with open(dictionarypath + 'given_names_dict.json', 'w') as f:
    json.dump(given_names_dict, f)

all_disambiguations = {}
for disambiguations in disambiguation_dicts:
    for title in disambiguations:
        candidates = disambiguations[title]
        all_disambiguations[title] = candidates
print('read json.')

new_redirects = {}
new_redirects_reversed = {}
new_redirects_reversed_upper = {}
new_redirects_upper = {}

disambiguation_dicts = [other_disambiguations,human_disambiguations,geo_disambiguations,number_disambiguations]

all_disambiguations = {}
for disambiguations in disambiguation_dicts:
    for title in disambiguations:
        candidates = disambiguations[title]
        all_disambiguations[title] = candidates

print('read json.')

for redirect in redirects:
    article = redirects[redirect]
    if not any(article.lower().startswith(ignore + ':') for ignore in IGNORED_NAMESPACES):
        new_redirects[redirect] = article

redirects = None

for article in articles:
    if not any(article.lower().startswith(ignore + ':') for ignore in IGNORED_NAMESPACES):
        if len(article) > 0 and article[0].isupper():
            lower_article = article[0].lower() + article[1:]
            if lower_article not in new_redirects:
                new_redirects[lower_article] = article

print('processed redirects')

with open(dictionarypath + 'redirects.json', 'w') as f:
    json.dump(new_redirects, f)


new_aliases = {}
for alias in aliases:
    candidates = aliases[alias]
    alias = alias.strip()

    if len(alias) == 0 or alias.lower() in stop:
        continue

    if alias.endswith(','):
        alias = alias[:-1]

    if not any(alias.lower().startswith(ignore + ':') for ignore in IGNORED_NAMESPACES):

        for candidate in candidates:
            if candidate not in all_disambiguations:
                counter = candidates[candidate]
                if candidate in new_redirects:
                    candidate = new_redirects[candidate]
                if alias not in new_aliases:
                    new_aliases[alias] = {}
                if candidate not in new_aliases[alias]:
                    new_aliases[alias][candidate] = 0
                new_aliases[alias][candidate] += counter

aliases = None

for disambiguation in all_disambiguations:
    candidates = all_disambiguations[disambiguation]
    alias = disambiguation
    pos = alias.find(' (')
    if pos > -1:
        alias = alias[:pos]

    if alias not in new_aliases:
        new_aliases[alias] = {}
    for candidate in candidates:
        if candidate not in new_aliases[alias]:
            new_aliases[alias][candidate] = 0
        new_aliases[alias][candidate] += 2

with open(dictionarypath + 'aliases.json', 'w') as f:
    json.dump(new_aliases, f)
print('processed aliases')

mostly_upper = set()
mostly_lower = set()

new_aliases_sorted = {}
for alias in new_aliases:
    candidates = new_aliases[alias]
    l = []
    new_aliases_sorted[alias] = {'dict':candidates}
    for candidate in candidates:
        l.append((candidate,candidates[candidate]))
    l.sort(key=lambda x:x[1],reverse=True)
    new_aliases_sorted[alias]['list'] = l

with open(dictionarypath + 'aliases_sorted.json', 'w') as f:
    json.dump(new_aliases_sorted, f)

print('processed aliases sorted')


new_aliases_reversed_sorted = {}
for alias in new_aliases_sorted:
    d = new_aliases_sorted[alias]['dict']
    l = new_aliases_sorted[alias]['list']
    for article in d:
        counter = d[article]
        if article not in new_aliases_reversed_sorted:
            new_aliases_reversed_sorted[article] = {'dict':{},'list':[]}
        new_aliases_reversed_sorted[article]['dict'][alias] = counter
        new_aliases_reversed_sorted[article]['list'].append((alias,counter))

for article in new_aliases_reversed_sorted:
    new_aliases_reversed_sorted[article]['list'].sort(key=lambda x:x[1],reverse=True)
    alias = new_aliases_reversed_sorted[article]['list'][0][0]
    if len(alias) > 0 and article not in given_names and article not in surnames and article not in other_disambiguations and \
            article not in human_disambiguations and article not in geo_disambiguations and article in articles:
        is_upper = False
        if alias[0].isupper():
            is_upper = True
        elif alias[0].isdigit() and not is_number(alias):
            for tuple in new_aliases_reversed_sorted[article]['list']:
                alias = tuple[0]
                if len(alias) > 0 and alias[0].isupper():
                    is_upper = True
                    break
                elif len(alias) > 0 and alias[0].islower():
                    break
        if is_upper and article.lower() not in stop:
            mostly_upper.add(article)
        else:
            mostly_lower.add(article)


with open(dictionarypath + 'mostly_upper.json', 'w') as f:
    json.dump(list(mostly_upper), f)

with open(dictionarypath + 'mostly_lower.json', 'w') as f:
    json.dump(list(mostly_lower), f)

with open(dictionarypath + 'aliases_reversed_sorted.json','w') as f:
    json.dump(new_aliases_reversed_sorted,f)

new_aliases = None
new_aliases_reversed_sorted = None

print('processed aliases reversed sorted and upper articles')

for redirect in new_redirects:
    article = new_redirects[redirect]
    if len(redirect) > 0 and article in mostly_upper and redirect[0].isupper():
        new_redirects_upper[redirect] = article

print('processed redirects upper')

for redirect in new_redirects:
    article = new_redirects[redirect]
    if article not in new_redirects_reversed:
        new_redirects_reversed[article] = []
    new_redirects_reversed[article].append(redirect)

print('processed redirects reversed')

for redirect in new_redirects_upper:
    article = new_redirects_upper[redirect]
    if article not in new_redirects_reversed_upper:
        new_redirects_reversed_upper[article] = []
    new_redirects_reversed_upper[article].append(redirect)

print('processed redirects reversed upper')



with open(dictionarypath + 'redirects_upper.json', 'w') as f:
    json.dump(new_redirects_upper, f)

with open(dictionarypath + 'redirects_reversed.json', 'w') as f:
    json.dump(new_redirects_reversed, f)

with open(dictionarypath + 'redirects_reversed_upper.json', 'w') as f:
    json.dump(new_redirects_reversed_upper, f)

print('wrote new redirects.')

new_redirects_upper = None
new_redirects_reversed = None
new_redirects_reversed_upper = None
new_redirects = None

print('processed aliases')



new_aliases_sorted_pruned = {}
for alias in new_aliases_sorted:
    d = new_aliases_sorted[alias]['dict']
    l = new_aliases_sorted[alias]['list']
    new_d = {}
    new_l = []
    for candidate in d:
        if not any(candidate.lower().startswith(ignore + ':') for ignore in IGNORED_NAMESPACES) and not candidate.startswith('List of'):
            new_d[candidate] = d[candidate]
    for tuple in l:
        if not any(tuple[0].lower().startswith(ignore + ':') for ignore in IGNORED_NAMESPACES) and not tuple[0].startswith('List of'):
            new_l.append(tuple)
    if len(new_d) > 0 and len(new_l) > 0:
        new_aliases_sorted_pruned[alias] = {'dict':new_d,'list':new_l}

new_aliases_reversed_sorted_pruned = {}
for alias in new_aliases_sorted_pruned:
    d = new_aliases_sorted_pruned[alias]['dict']
    l = new_aliases_sorted_pruned[alias]['list']
    for article in d:
        counter = d[article]
        if article not in new_aliases_reversed_sorted_pruned:
            new_aliases_reversed_sorted_pruned[article] = {'dict':{},'list':[]}
        new_aliases_reversed_sorted_pruned[article]['dict'][alias] = counter
        new_aliases_reversed_sorted_pruned[article]['list'].append((alias,counter))

for article in new_aliases_reversed_sorted_pruned:
    new_aliases_reversed_sorted_pruned[article]['list'].sort(key=lambda x:x[1],reverse=True)

with open(dictionarypath + 'aliases_sorted_pruned.json', 'w') as f:
    json.dump(new_aliases_sorted_pruned, f)



with open(dictionarypath + 'aliases_reversed_sorted_pruned.json','w') as f:
    json.dump(new_aliases_reversed_sorted_pruned,f)

new_aliases_sorted = None
new_aliases_reversed_sorted_pruned = None
print('processed aliases sorted pruned')


new_aliases_sorted_pruned_upper = {}
for alias in new_aliases_sorted_pruned:
    if len(alias) > 0 and alias[0].isupper():
        d = new_aliases_sorted_pruned[alias]['dict']
        l = new_aliases_sorted_pruned[alias]['list']
        new_d = {}
        new_l = []
        for candidate in d:
            if candidate in mostly_upper:
                new_d[candidate] = d[candidate]
        for tuple in l:
            if tuple[0] in mostly_upper:
                new_l.append(tuple)

        if len(new_d) > 0 and len(new_l) > 0:
            new_aliases_sorted_pruned_upper[alias] = {'dict':new_d,'list':new_l}

new_aliases_reversed_sorted_pruned_upper = {}
entity_popularity = {}
for alias in new_aliases_sorted_pruned_upper:
    d = new_aliases_sorted_pruned_upper[alias]['dict']
    l = new_aliases_sorted_pruned_upper[alias]['list']
    for article in d:
        counter = d[article]
        if article not in new_aliases_reversed_sorted_pruned_upper:
            new_aliases_reversed_sorted_pruned_upper[article] = {'dict':{},'list':[]}
        new_aliases_reversed_sorted_pruned_upper[article]['dict'][alias] = counter
        new_aliases_reversed_sorted_pruned_upper[article]['list'].append((alias,counter))

        if article not in entity_popularity:
            entity_popularity[article] = 0

        entity_popularity[article] += counter

for article in new_aliases_reversed_sorted_pruned_upper:
    new_aliases_reversed_sorted_pruned_upper[article]['list'].sort(key=lambda x:x[1],reverse=True)

with open(dictionarypath + 'aliases_sorted_pruned_upper.json', 'w') as f:
    json.dump(new_aliases_sorted_pruned_upper, f)

with open(dictionarypath + 'aliases_reversed_sorted_pruned_upper.json','w') as f:
    json.dump(new_aliases_reversed_sorted_pruned_upper,f)

print('processed aliases sorted pruned upper')

popular_entities = []
for entity in entity_popularity:
    popular_entities.append((entity,entity_popularity[entity]))

popular_entities.sort(key=lambda x:x[1],reverse=True)

most_popular_entities = []
for i in range(min(10000,len(popular_entities))):
    most_popular_entities.append(popular_entities[i][0])

with open(dictionarypath + 'most_popular_entities_10000.json','w') as f:
    json.dump(most_popular_entities,f)
