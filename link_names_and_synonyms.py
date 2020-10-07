import sys

from src.helpers.wikipedia_corpus import WikipediaCorpus
from src.models.entity_database import EntityDatabase
from src.name_and_synonym_entity_linker import NameAndSynonymEntityLinker


def print_help():
    print("Usage:\n"
          "    python3 link_names_and_synonyms.py <corpus_file> <entity_file> <person_names_file> <out_file>\n"
          "\n"
          "Examples:\n"
          "    python3 link_names_and_synonyms.py"
          " ~/wikipedia/wikipedia_2020-06-08/1000_articles_with_links_mapped+NERed.txt"
          " ~/wikipedia/wikipedia_2020-06-08/yi-chun/wikidata-entities-large.tsv"
          " ~/wikipedia/wikipedia_2020-06-08/yi-chun/wikidata-familyname.csv"
          " ~/wikipedia/wikipedia_2020-06-08/1000_articles_with_links_mapped+NERed+names.txt\n"
          "    python3 link_names_and_synonyms.py"
          " /local/data/hertelm/wikipedia_2020-06-08/articles_with_links_mapped+NERed.txt"
          " /local/data/hertelm/wikipedia_2020-06-08/yi-chun/wikidata-entities-large.tsv"
          " /local/data/hertelm/wikipedia_2020-06-08/yi-chun/wikidata-familyname.csv"
          " /local/data/hertelm/wikipedia_2020-06-08/articles_with_links_mapped+NERed+names.txt")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print_help()
        exit(1)

    corpus_file = sys.argv[1]
    entity_file = sys.argv[2]
    person_names_file = sys.argv[3]
    out_file = sys.argv[4]

    corpus = WikipediaCorpus(corpus_file)
    entity_db = EntityDatabase(entity_file)
    entity_linker = NameAndSynonymEntityLinker(entity_db, person_names_file)

    with open(out_file, "w", encoding="utf8") as out_file:
        for a_i, article in enumerate(corpus.get_articles()):
            for paragraph in article.paragraphs:
                entity_linker.link_entities(paragraph)
            print("\r%i articles: %i new entities (%i by name, %i by synonym)" %
                  (a_i + 1, entity_linker.linked_by_name + entity_linker.linked_by_synonym, entity_linker.linked_by_name,
                   entity_linker.linked_by_synonym),
                  end='')
            out_file.write(article.to_json() + '\n')
        print()
