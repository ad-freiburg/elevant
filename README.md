# Wikipedia-to-Wikidata Entity Linker

## Steps

1. Download a Wikipedia dump.
2. Get the following files (by Yi-Chun Lin; the files are currently located at /nfs/students/yi-chun-lin/database):
    + wikidata-wikipedia-mapping.csv
    + wikidata-familyname.csv
    + wikidata-entities-large.tsv
    + wikidata-wikipedia.tsv
3. Extract articles and paragraphs from the dump:
    + python3 parse_wikipedia_dump.py
4. Link entities from article references:
    + python3 link_page_references.py
5. Shuffle the paragraphs and split them into training, development and test:
    + python3 shuffle_paragraphs.py
    + python3 split_paragraphs.py
6. Generate word vectors:
    + python3 create_word_vectors.py 0
7. Create the knowledge base:
    + python3 create_knowledge_base.py 0
8. Train the entity linker:
    + python3 train_entity_linker.py
9. Evaluate the entity linker:
    + python3 test_entity_linker.py
10. Link entities in the extracted articles:
    + python3 link_wiki_entities.py
11. Print paragraphs with entity annotations:
    + python3 print_paragraphs_with_entities.py

### Old

5. Recognize additional entities with spaCy:
    + python3 recognize_entities.py
6. Link entities by their names and synonyms:
    + python3 link_names_and_synonyms.py
7. Print the result:
    + python3 print_paragraphs_with_entities.py
