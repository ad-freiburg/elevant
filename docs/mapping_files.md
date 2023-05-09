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

* **`qid_to_label.tsv`**: QID and English label for all entities in Wikidata. *This file is an intermediate file used
 only to generate a Python database and is therefore not contained in the downloaded files. If you generate the Wikidata
 mappings yourself, this file will be removed if you run the `make cleanup` command.* Example entry:

      Q1	universe

* **`qid_to_label.db`**: Same as `qid_to_label.tsv` but stored as a Python dbm database where the QIDs are the keys
 and the labels are the values.

* **`label_to_qids.db`**: Same as `qid_to_label.db` but the labels are the database keys and the QIDs the values.

* **`qid_to_gender.tsv`**: QID and 'sex or gender' property label for all entities in Wikidata. Example entry:

      Q100151573	transgender female

* **`qid_to_name.tsv`**: QID and label for all entities of type 'human' in Wikidata. Example entry:

      Q10000001	Tatyana Kolotilshchikova

* **`qid_to_sitelinks.tsv`**: QID and sitelink count for all entities in Wikidata. *This file is an intermediate file
 used only to generate a Python database and is therefore not contained in the downloaded files. If you generate the
 Wikidata mappings yourself, this file will be removed if you run the `make cleanup` command.* Example entry:

      Q1	203

* **`qid_to_sitelinks.db`**:  Same as `qid_to_sitelink.tsv` but stored as a Python dbm database where the QIDs are the
 keys and the sitelink counts are the values.

* **`qid_to_aliases.tsv`**: QID and synonyms for all entities in Wikidata. *This file is an intermediate file used
 only to generate a Python database and is therefore not contained in the downloaded files. If you generate the Wikidata
 mappings yourself, this file will be removed if you run the `make cleanup` command.* Example entry:

      Q1	all;cosmos;creation;existence;Heaven and earth;macrocosm;metagalaxy;Our Universe;outer space;space;system;The Cosmos;The Universe;Universe;world;Yin and Yang

* **`qid_to_aliases.db`**: Same as `qid_to_aliases.tsv` but stored as a Python dbm database where the QIDs are the
 keys and the aliases are the values.

 * **`alias_to_qids.db`**: Same as `qid_to_aliases.db` but the aliases are the database keys and the QIDs the values.

* **`qid_to_wikipedia_url.tsv`**: QID and Wikipedia URL for all entities in Wikidata that exist in Wikipedia. *This
 file is an intermediate file used only to generate a Python database and is therefore not contained in the
 downloaded files. If you generate the Wikidata mappings yourself, this file will be removed if you run the
 `make cleanup` command.* Example entry:

      Q1	https://en.wikipedia.org/wiki/Universe

* **`wikipedia_name_to_qid.db`**: Same as `qid_to_wikipedia_url.tsv` but stored as a Python dbm database where the
 Wikipedia names (extracted from the Wikipedia URLs) are the database keys and the QIDs are the values.


The following files are only needed if you want to use coreference resolution in addition to entity linking:

*  **`qid_to_p31.tsv`**: QID and 'instance of' property for all entities in Wikidata. *This file is an intermediate
 file used only to generate the `qid_to_coreference_types.tsv` file and is therefore not contained in the downloaded
 files. If you generate the Wikidata mappings yourself, this file will be removed if you run the `make cleanup`
 command.* Example entry:

       Q1	Q36906466

* **`qid_to_p279.tsv`**: QID and 'subclass of' property for all entities in Wikidata. *This file is an intermediate
 file used only to generate the `qid_to_coreference_types.tsv` file and is therefore not contained in the downloaded
 files. If you generate the Wikidata mappings yourself, this file will be removed if you run the `make cleanup`
 command.* Example entry:

      Q105	Q573

* **`qid_to_all_types.tsv`**: QID and all corresponding types and their level in the type hierarchy for all entities
 in Wikidata with a sitelink count >= 2. *This file is an intermediate file used
 only to generate the `qid_to_coreference_types.tsv` file and is therefore not contained in the downloaded files. If you
 generate the Wikidata mappings yourself, this file will be removed if you run the `make cleanup` command.* Example
 entry:

      Q1	0:Q36906466	1:Q1454986	1:Q16686022	2:Q223557	2:Q29651224	2:Q58778	3:Q35459920	3:Q4406616	3:Q488383	3:Q6671777	4:Q35120

* **`qid_to_coreference_types.tsv`**: QID and all corresponding types that are deemed important for nominal
 coreference for all entities in Wikidata with a sitelink count >= 2. Example entry:

      Q1	Q36906466;Q1454986;Q16686022;Q223557;Q29651224;Q58778;Q35459920;Q4406616;Q488383;Q6671777
 
 
In total, the Wikidata mapping files require about 30GB of disk space (this can vary depending on the Wikidata
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

* **`hyperlink_frequencies.pkl`**: Pickled Python dictionary that maps link anchor texts to a dictionary of link target
 QIDs and their corresponding link frequencies. Hyperlink frequencies are computed over the Wikipedia training split.
 Example dictionary entry:

      >>> hyperlink_frequencies["Gandalf"]
      {'Q177499': 322, 'Q208870': 3, 'Q4133209': 2, 'Q3095082': 5, 'Q587350': 2, 'Q220967': 4}

* **`hyperlink_to_most_popular_candidates.db`**: Python dbm database that maps link anchor texts to its set of QIDs
 with the highest link frequency. Example database entry:

      >>> hyperlink_to_most_popular_candidates["Gandalf"]
      {'Q177499'}

* **`redirects.pkl`**: Pickled Python dictionary that maps redirect page titles to their corresponding redirect
 target. *This file is an intermediate file used only to generate a Python database and is therefore not contained in
 the downloaded files. If you generate the Wikipedia mappings yourself, this file will be removed if you run the
 `make cleanup` command.* Redirects are extracted from the entire Wikipedia dump. Example dictionary entry:

      >>> redirects["Barack H. Obama"]
      'Barack Obama'

* **`redirects.db`**: Same as `redirects.pkl` but stored as a Python dbm database where the redirect page titles are the
 keys and the redirect targets are the values.

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

In total, the Wikipedia mapping files require about 5GB of disk space (this can vary depending on the Wikipedia
 version used to generate the mappings).

## Entity-Type Mapping

The following file is generated in `<data_directory>/wikidata-mappings/` when running `make
 generate_entity_types_mapping` or downloaded when running `make download_entity_types_mapping`:
* **`entity-types.tsv`**: QID and corresponding whitelist type for all entities in Wikidata. *This file will be
 removed if you run the `make cleanup` command, since it has been transformed into a database for faster retrieval.*
 Example entry:

      Q100	Q27096213


* **`qid_to_whitelist_types.db`**: Same as `entity-types.tsv` but stored as a Python dbm database where the QIDs are the
 database keys and the whitelist types are the values.