# Wikipedia-to-Wikidata Entity Linker

## Usage

### 1. Extract articles with links from a Wikipedia dump

1. Download a Wikipedia dump, e.g. the latest one:
    + wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles-multistream.xml.bz2
2. Get the WikiExtractor script:
    + wget https://github.com/attardi/wikiextractor/blob/master/WikiExtractor.py
3. Extract articles in JSON format, keeping the link information:
    + python3 WikiExtractor.py -o json --json --links enwiki-latest-pages-articles-multistream.xml.bz2

### 2. Get data for the Entity Linker

1. Get the following files (by Yi-Chun Lin; the files are currently located at /nfs/students/yi-chun-lin/database):
    + wikidata-wikipedia-mapping.csv
    + wikidata-familyname.csv
    + wikidata-entities-large.tsv
    + wikidata-wikipedia.tsv
2. Count the link texts:
    + python3 get_link_frequencies.py
3. (optional) Print the link frequencies:
    + python3 print_link_frequencies.py

### 3. Initialize and train the Entity Linker

1. Generate word vectors:
    + python3 create_word_vectors.py 0
2. Create the knowledge base:
    + python3 create_knowledge_base.py 0
3. Train the entity linker:
    + python3 train_entity_linker.py

### 4. Test and use the trained Entity Linker

1. Evaluate the entity linker:
    + python3 test_entity_linker.py
2. Link entities in the extracted articles:
    + python3 link_wiki_entities.py
3. Print paragraphs with entity annotations:
    + python3 print_paragraphs_with_entities.py
