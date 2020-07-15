# Wikipedia-to-Wikidata Entity Linker

## Docker/wharfer instructions

Get the code, and build and start the container:

    git clone git@github.com:ad-freiburg/wiki_entity_linker.git .
    wharfer build -t wiki-entity-linker .
    wharfer run -it -v /nfs/students/matthias-hertel/wiki_entity_linker:/data wiki-entity-linker

Once the container is started, evaluate the trained entity linker, or one of the baselines:

    python3 test_entity_linker.py

## Usage

### 1. Extract articles with links from a Wikipedia dump

1. Download a Wikipedia dump, e.g. the latest one:

       wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles-multistream.xml.bz2
2. Extract articles in JSON format, keeping the link information:

       python3 src/wiki_extractor/WikiExtractor.py --links --json --output_file json/wiki_extracted.json enwiki-latest-pages-articles-multistream.xml.bz2
### 2. Get data for the Entity Linker

(These steps can be skipped. The resulting files are already on `/nfs/students/matthias-hertel/wiki_entity_linker`.)

1. Get the following files (by Yi-Chun Lin; the files are currently located at `/nfs/students/yi-chun-lin/database`):
    + wikidata-wikipedia-mapping.csv
    + wikidata-familyname.csv
    + wikidata-entities-large.tsv
    + wikidata-wikipedia.tsv
2. Count the link texts:

       python3 get_link_frequencies.py
3. (optional) Print the link frequencies:

       python3 print_link_frequencies.py

### 3. Initialize and train the Entity Linker

(These steps can be skipped. The resulting files are already on `/nfs/students/matthias-hertel/wiki_entity_linker`.)
1. Generate word vectors:

       python3 create_word_vectors.py 0
2. Create the knowledge base:

       python3 create_knowledge_base.py 0
3. Train the entity linker:

       python3 train_entity_linker.py

### 4. Test and use the trained Entity Linker

1. Evaluate the entity linker:

       python3 test_entity_linker.py
2. Link entities in the extracted articles:

       python3 link_wiki_entities.py
3. Print paragraphs with entity annotations:

       python3 print_paragraphs_with_entities.py
