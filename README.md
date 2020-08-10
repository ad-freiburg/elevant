# Wikipedia-to-Wikidata Entity Linker

## Docker/wharfer instructions

Get the code, and build and start the container:

    git clone git@github.com:ad-freiburg/wiki_entity_linker.git .
    wharfer build -t wiki-entity-linker .
    wharfer run -it -v /nfs/students/matthias-hertel/wiki_entity_linker:/data wiki-entity-linker

Once the container is started, evaluate the trained entity linker, or one of the baselines:

    python3 test_entity_linker.py spacy linker development.txt 1000
    python3 test_entity_linker.py baseline links development.txt 1000
    python3 test_entity_linker.py baseline scores development.txt 1000

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

## Evaluation script calls

### Wikipedia benchmark

baseline:

    python3 test_entity_linker.py baseline links-all wikipedia 1000

spaCy data files (entities and aliases queried from Wikidata):

    python3 test_entity_linker.py spacy prior_trained wikipedia 1000

spaCy wikipeida (entities and aliases extracted from a Wikipedia dump):

    python3 test_entity_linker.py spacy wikipedia wikipedia 1000 -kb wikipedia

Explosion's spaCy:

    python3 test_entity_linker.py explosion /nfs/students/matthias-hertel/wiki_entity_linker/linker-1M/nlp wikipedia 1000

Ambiverse:

    python3 test_entity_linker.py ambiverse /nfs/students/natalie-prange/src/ambiverse-nlu/dev_set_1k_results/ wikipedia 1000

### CoNLL benchmark:
baseline:

    python3 test_entity_linker.py baseline links-all conll -1

spaCy data files:

    python3 test_entity_linker.py spacy prior_trained conll -1

spaCy wikipedia:

    python3 test_entity_linker.py spacy wikipedia conll -1 -kb wikipedia

Explosion's spaCy:

    python3 test_entity_linker.py explosion /nfs/students/matthias-hertel/wiki_entity_linker/linker-1M/nlp conll -1

Ambiverse:

    python3 test_entity_linker.py iob /nfs/students/yi-chun-lin/outputs/conll/conll-wikidata-iob-annotations.alg-ambiverse conll -1

### Own benchmark:
baseline:

    python3 test_entity_linker.py baseline links-all own -1

spaCy data files:

    python3 test_entity_linker.py spacy prior_trained own -1

spaCy wikipedia:

    python3 test_entity_linker.py spacy wikipedia own -1 -kb wikipedia

Explosion's spaCy:

    python3 test_entity_linker.py explosion /nfs/students/matthias-hertel/wiki_entity_linker/linker-1M/nlp own -1

Ambiverse:

    python3 test_entity_linker.py ambiverse /nfs/students/natalie-prange/src/ambiverse-nlu/own_benchmark_results/ own -1

Link-Text-Linker + spaCy wikipedia

    python3 test_entity_linker.py spacy wikipedia own -1 -kb wikipedia -link_linker link-text-linker

Link-Linker + Explosion

    python3 test_entity_linker.py explosion /nfs/students/matthias-hertel/wiki_entity_linker/linker-1M/nlp own -1 -link_linker link-linker

Link-Text-Linker + Explosion

    python3 test_entity_linker.py explosion /nfs/students/matthias-hertel/wiki_entity_linker/linker-1M/nlp own -1 -link_linker link-text-linker

Link-Text-Linker + Explosion + Coref

    python3 test_entity_linker.py explosion /nfs/students/matthias-hertel/wiki_entity_linker/linker-1M/nlp own -1 -link_linker link-text-linker -coref
