# List of Mapping Files
## Wikidata Mappings
The following files are generated in `<data_directory>/wikidata_mappings/` when running
`make generate_wikidata_mappings` or downloaded when running `make download_wikidata_mappings`:

* **`qid_to_demonym.tsv`**: QID and corresponding demonym for all demonyms in Wikidata. Example entry:
        
      Q100	Bostonian

* **`qid_to_language.tsv`**: QID and label for all entities of type 'language' in Wikidata. Example entry:

      Q100103	West Flemish

* **`quantity.tsv`**: QID of all entities of type 'real number' in Wikidata. Example entry:

      Q100286778

* **`datetime.tsv`**: QID of all entities of type 'point in time' in Wikidata. Example entry:

      Q100594618

* **`qid_to_label.tsv`**: QID and English label for all entities in Wikidata. Example entry:

      Q1	universe

* **`qid_to_gender.tsv`**: QID and 'sex or gender' property label for all entities in Wikidata. Example entry:

      Q100151573	transgender female

* **`qid_to_name.tsv`**: QID and label for all entities of type 'human' in Wikidata. Example entry:

      Q10000001	Tatyana Kolotilshchikova

* **`qid_to_sitelink.tsv`**: QID and sitelink count for all entities in Wikidata. Example entry:

      Q1	203

* **`qid_to_aliases.tsv`**: QID, label and synonyms (if existing) for all entities in Wikidata that exist
 in Wikipedia. Example entry:

      Q1	universe	all;cosmos;creation;existence;Heaven and earth;macrocosm;metagalaxy;Our Universe;outer space;space;system;The Cosmos;The Universe;Universe;world;Yin and Yang

* **`qid_to_wikipedia_url.tsv`**: QID and Wikipedia URL for all entities in Wikidata that exist in Wikipedia. Example
 entry:

      Q1	https://en.wikipedia.org/wiki/Universe

*  **`qid_to_p31.tsv`**: QID and 'instance of' property for all entities in Wikidata. Example entry:

       Q1	Q36906466

* **`qid_to_p279.tsv`**: QID and 'subclass of' property for all entities in Wikidata. Example entry:

      Q105	Q573

The following two files are only needed if you want to use coreference resolution in addition to entity linking:
* **`qid_to_all_types.tsv`**: QID and all corresponding types and their level in the type hierarchy for all entities
 in Wikidata with a sitelink count >= 2. Example entry:

      Q1	0:Q36906466	1:Q1454986	1:Q16686022	2:Q223557	2:Q29651224	2:Q58778	3:Q35459920	3:Q4406616	3:Q488383	3:Q6671777	4:Q35120

* **`qid_to_coreference_types.tsv`**: QID and all corresponding types that are deemed important for nominal
 coreference for all entities in Wikidata with a sitelink count >= 2. Example entry:

      Q1	Q36906466;Q1454986;Q16686022;Q223557;Q29651224;Q58778;Q35459920;Q4406616;Q488383;Q6671777
 
 
In total, the Wikidata mapping files require about 14GB of disk space (this can vary depending on the Wikidata
 version used to generate the mappings).
 
 
## Wikipedia Mappings
The following files are generated in `<data_directory>/wikipedia_dump_files/` when running
 `make generate_wikipedia_mappings` (but are not downloaded when running `make download_wikipedia_mappings`):

* **`enwiki-latest-pages-articles-multistream.xml.bz2`**: The latest dump of the English Wikipedia. This file can
 also be created individually by running `make download_wiki`.
* **`enwiki-latest-extracted.jsonl`**: The extracted version of the latest Wikipedia dump. The extracted version
 contains only articles. Other pages like redirect pages are filtered out. This file can also be created
 individually by running `make extract_wiki`.

The following files are generated in `<data_directory>/articles/wikipedia/` when running
 `make generate_wikipedia_mappings` (but are not downloaded when running `make download_wikipedia_mappings`):
* **`training.jsonl`**: Training split of the extracted Wikipedia dump.
* **`development.jsonl`**: Development split of the extracted Wikipedia dump.
* **`test.jsonl`**: Test split of the extracted Wikipedia dump.

These three files can also be created individually by running `make split_wiki`.

The following files are generated in `<data_directory>/wikipedia_mappings/` when running
 `make generate_wikipedia_mappings` or downloaded when running `make download_wikipedia_mappings`:
* **`akronyms.pkl`**: Pickled Python dictionary that maps akronyms to sets of corresponding Wikipedia titles.
 Akronyms are extracted from Wikipedia hyperlinks that are followed by uppercase letters in brackets. E.g.
 "[Baranov_Central Institute of Aviation Motor Development](https://en.wikipedia.org/wiki/Central_Institute_of_Aviation_Motors) (CIAM)"
 would lead to the dictionary entry `akronyms["CIAM"] = {..., Central Institute of Aviation Motors}`. Akronyms are
 extracted from articles in the Wikipedia training split only. Example dictionary entry:

      >>> akronyms["CIAM"]
      {"Congres Internationaux d'Architecture Moderne", 'Central Institute of Aviation Motors', "Congrès Internationaux d'Architecture Moderne", "Congrès International d'Architecture Moderne#Influence", "Congrès International d'Architecture Moderne"}

* **`article_abstracts.tsv`**: Article ID, title, url and abstract for all articles in the Wikipedia dump. Abstracts
 are defined as the text in the article up to the first `\n\n`. Example entry:

      12	Anarchism	https://en.wikipedia.org/wiki?curid=12	Anarchism is a political philosophy and movement that is sceptical of authority [...]

* **`link_frequencies.pkl`**: Pickled Python dictionary that maps link anchor texts to a dictionary of link targets
 and their corresponding link frequencies. Link frequencies are computed over the Wikipedia training split. Example
 dictionary entry:

      >>> link_frequencies["Gandalf"]
      {'Gandalf': 321, 'Gandalf (musician)': 2, 'Gandalf Alfgeirsson': 2, 'Gandalf (American band)': 5, 'Gandalf (Norse mythology)': 1, 'Gandalf (Finnish band)': 4, 'Gandalf (mythology)': 1, 'Gandalf (new age)': 1, 'Gandalf the Grey': 1}

* **`link_redirects.pkl`**: Pickled Python dictionary that maps redirect page titles to their corresponding redirect
 target. Redirects are extracted from the entire Wikipedia dump.  Example dictionary entry:

      >>> redirects["Barack H. Obama"]
      'Barack Obama'

* **`title_synonyms.pkl`**: Pickled Python dictionary that maps title synonyms to sets of corresponding Wikipedia
 titles. Title synonyms refer to the synonyms of a Wikipedia article title that appear in bold in the first paragraph
 of a Wikipedia article. E.g. the first sentence of the article "Gandalf (musician)": "**Gandalf** (born **Heinz
 Strobl**, born 1952) is an Austrian new-age composer.", would lead to the dictionary entries
 `title_synonyms["Gandalf"] = {..., "Gandalf (musician)"}`and
 `title_synonyms["Heinz Strobl"] = {..., "Gandalf (musician)"}`. Title synonyms are extracted from the Wikipedia
 training split. Example dictionary entry:

      >>> title_synonyms["Gandalf"]
      {'Gandalf (musician)', 'Gandalf (mythology)', 'Gandalf', 'Gandalf (disambiguation)', 'Gandalf (American band)', 'Gandalf Technologies', 'Gandalf (Finnish band)'}

* **`unigrams.txt`**: Word and its corresponding frequency in the Wikipedia dump for all words in the dump. Example
 entry:

      corresponding 56483

* **`wikipedia_id_to_title.tsv`**: Wikipedia article ID and Wikipedia article title for all articles in the Wikipedia
 dump. Example entry:

      12	Anarchism

* **`qid_to_wikipedia_abstract.tsv`**: QID, Wikipedia title and Wikipedia abstract for each article in the Wikipedia
 dump. Abstracts are defined as the text in the first section of an article (which can include several paragraphs
 separated by `\n\n`). The files `<data_directory>/wikipedia_mappings/link_redirects.pkl` and
 `<data_directory>/wikidata_mappings/qid_to_wikipedia_url.tsv` are needed to create this file. Example entry:

      Q6199	Anarchism	Anarchism is a political philosophy and movement that is sceptical of authority [...]

In total, the Wikipedia mapping files require about 7GB of disk space (this can vary depending on the Wikipedia
 version used to generate the mappings).

## Entity-Type Mapping

The following file is generated in `<data_directory>/wikidata-mappings/` when running `make
 generate_entity_types_mapping` or downloaded when running `make download_entity_types_mapping`:
* **`entity-types.tsv`**: QID and corresponding whitelist type for all entities in Wikidata. Example entry:

      Q100	Q27096213
      
The entity-type mapping file requires about 1.4GB of disk space (this can vary depending on the Wikidata version used
 to generate the mapping).
