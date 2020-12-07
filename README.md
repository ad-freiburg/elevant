# Wikipedia-to-Wikidata Entity Linker

## Docker/wharfer instructions

Get the code, and build and start the container:

    git clone git@github.com:ad-freiburg/wiki_entity_linker.git .
    wharfer build -t wiki-entity-linker .
    wharfer run -it -v /nfs/students/matthias-hertel/wiki_entity_linker:/data wiki-entity-linker

Once the container is started, type `make help` to get some predefined evaluation targets or see section
*Evaluation script calls* for more details.

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

1. Link entities over a specified benchmark:

       python3 link_benchmark_entities.py [-h]
                                          [-b {own,wikipedia,conll}]
                                          [-n N_ARTICLES]
                                          [-kb {wikipedia}]
                                          [-ll {link-linker,link-text-linker}]
                                          [-coref {neuralcoref,entity,stanford,xrenner,hobbs}]
                                          [--only_pronouns]
                                          [--evaluation_span]
                                          [-min MINIMUM_SCORE]
                                          [-small]
                                          [--longest_alias_ner]
                                          [--uppercase]
                                          output_file
                                          {baseline,spacy,explosion,ambiverse,iob,tagme,none}
                                          linker

2. Evaluate the linked entities from (1):

        python3 evaluate_linked_entities.py [-h]
                                            [-out OUTPUT_FILE]
                                            [-in INPUT_CASE_FILE]
                                            [--no_coreference]
                                            input_file

3. Link entities in the extracted articles:

       python3 link_entities.py [-h]
                                [-raw]
                                [-n N_ARTICLES]
                                [-kb {wikipedia}]
                                [-ll {link-linker,link-text-linker}]
                                [-coref {neuralcoref,entity,stanford,xrenner,hobbs}]
                                [--only_pronouns]
                                [-min MINIMUM_SCORE]
                                [-small]
                                [--longest_alias_ner]
                                [--uppercase]
                                input_file
                                output_file
                                {baseline,spacy,explosion,ambiverse,iob,tagme,none}
                                linker

4. Print articles with entity annotations:

       python3 print_linked_entities.py [-h]
                                        input_file

## Evaluation script calls

### Wikipedia benchmark

baseline:

    python3 link_benchmark_entities.py <output_file> baseline links-all -b wikipedia -n 1000

spaCy data files (entities and aliases queried from Wikidata):

    python3 link_benchmark_entities.py <output_file> spacy prior_trained -b wikipedia -n 1000

spaCy wikipeida (entities and aliases extracted from a Wikipedia dump):

    python3 link_benchmark_entities.py <output_file> spacy wikipedia -b wikipedia -n 1000 -kb wikipedia

Explosion's spaCy:

    python3 link_benchmark_entities.py <output_file> explosion /nfs/students/matthias-hertel/wiki_entity_linker/linker-1M/nlp -b wikipedia -n 1000

Ambiverse:

    python3 link_benchmark_entities.py <output_file> ambiverse /nfs/students/natalie-prange/src/ambiverse-nlu/dev_set_1k_results/ -b wikipedia -n 1000

### CoNLL benchmark:
baseline:

    python3 link_benchmark_entities.py <output_file> baseline links-all -b conll

spaCy data files:

    python3 link_benchmark_entities.py <output_file> spacy prior_trained -b conll

spaCy wikipedia:

    python3 link_benchmark_entities.py <output_file> spacy wikipedia -b conll -kb wikipedia

Explosion's spaCy:

    python3 link_benchmark_entities.py <output_file> explosion /nfs/students/matthias-hertel/wiki_entity_linker/linker-1M/nlp -b conll

Ambiverse:

    python3 link_benchmark_entities.py <output_file> iob /nfs/students/yi-chun-lin/outputs/conll/conll-wikidata-iob-annotations.alg-ambiverse -b conll

### Own benchmark:
baseline:

    python3 link_benchmark_entities.py <output_file> baseline links-all

spaCy data files:

    python3 link_benchmark_entities.py <output_file> spacy prior_trained

spaCy wikipedia:

    python3 link_benchmark_entities.py <output_file> spacy wikipedia -kb wikipedia

Explosion's spaCy:

    python3 link_benchmark_entities.py <output_file> explosion /nfs/students/matthias-hertel/wiki_entity_linker/linker-1M/nlp

Ambiverse:

    python3 link_benchmark_entities.py <output_file> ambiverse /nfs/students/natalie-prange/src/ambiverse-nlu/own_benchmark_results/

Link-Text-Linker + spaCy wikipedia

    python3 link_benchmark_entities.py <output_file> spacy wikipedia -kb wikipedia --link_linker link-text-linker

Link-Linker + Explosion

    python3 link_benchmark_entities.py <output_file> explosion /nfs/students/matthias-hertel/wiki_entity_linker/linker-1M/nlp --link_linker link-linker

Link-Text-Linker + Explosion

    python3 link_benchmark_entities.py <output_file> explosion /nfs/students/matthias-hertel/wiki_entity_linker/linker-1M/nlp --link_linker link-text-linker

Link-Text-Linker + Explosion + Entity Coref

    python3 link_benchmark_entities.py <output_file> explosion /nfs/students/matthias-hertel/wiki_entity_linker/linker-1M/nlp --link_linker link-text-linker -coref entity
