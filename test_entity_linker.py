from typing import Tuple, Optional, Set

import sys
from termcolor import colored

from src.trained_entity_linker import TrainedEntityLinker
from src.alias_entity_linker import AliasEntityLinker, LinkingStrategy
from src.entity_database_new import EntityDatabase
from src.wikipedia_dump_reader import WikipediaDumpReader
from src.ambiverse_prediction_reader import AmbiversePredictionReader
from src import settings


class Case:
    def __init__(self,
                 true_span: Tuple[int, int],
                 link_target: str,
                 true_entity: str,
                 predicted_span: Tuple[int, int],
                 predicted_entity: Optional[str],
                 candidates: Set[str]):
        self.true_span = true_span
        self.link_target = link_target
        self.true_entity = true_entity
        self.predicted_span = predicted_span
        self.predicted_entity = predicted_entity
        self.candidates = candidates

    def is_known_entity(self):
        return self.true_entity is not None

    def is_detected(self):
        return self.predicted_span is not None

    def is_correct(self):
        return self.predicted_entity is not None and self.true_entity == self.predicted_entity

    def true_entity_is_candidate(self):
        return self.true_entity in self.candidates

    def n_candidates(self):
        return len(self.candidates)

    def print_color(self):
        if not self.is_known_entity():
            return None
        if not self.is_detected():
            return "blue"
        if not self.true_entity_is_candidate():
            return "yellow"
        if self.is_correct():
            return "green"
        else:
            return "red"


def percentage(nominator: int, denominator: int) -> Tuple[float, int, int]:
    if denominator == 0:
        percent = 0
    else:
        percent = nominator / denominator * 100
    return percent, nominator, denominator


def print_help():
    print("Usage:\n"
          "    For a spaCy entity linker:\n"
          "        python3 test_entity_linker.py spacy <linker_name> <file> <n_articles>\n"
          "    For a baseline entity linker:\n"
          "        python3 test_entity_linker.py baseline <strategy> <file> <n_articles> [<minimum_score>]\n"
          "    To evaluate ambiverse results:\n"
          "        python3 test_entity_linker.py ambiverse <result_dir> <file> <n_articles>\n"
          "\n"
          "Arguments:\n"
          "    <linker_name>: Name of the saved spaCy entity linker.\n"
          "    <file>: Name of the file with evaluation articles, e.g. development.txt or test.txt.\n"
          "    <n_articles>: Number of development articles to evaluate on.\n"
          "    <strategy>: Choose one out of {links, scores}.\n"
          "        links:     Baseline using link frequencies for disambiguation.\n"
          "        scores:    Baseline using entity scores for disambiguation.\n"
          "        links-all: Baseline using link frequencies for disambiguation and more candidates.\n"
          "    <minimum_score>: For the baseline linkers, link no entities with a score lower than minimum_score."
          " Default is 0.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_help()
        exit(1)

    linker_type = sys.argv[1]
    if linker_type not in ("spacy", "ambiverse", "baseline"):
        raise NotImplementedError("Unknown linker type '%s'." % linker_type)

    if linker_type == "spacy":
        linker_name = sys.argv[2]
        linker = TrainedEntityLinker(linker_name)
    elif linker_type == "ambiverse":
        result_dir = sys.argv[2]
        ambiverse_prediction_iterator = AmbiversePredictionReader.article_predictions_iterator(result_dir)
    else:
        strategy_name = sys.argv[2]
        if strategy_name not in ("links", "scores", "links-all"):
            raise NotImplementedError("Unknown strategy '%s'." % strategy_name)
        minimum_score = int(sys.argv[5]) if len(sys.argv) > 5 else 0
        entity_db = EntityDatabase()
        if strategy_name in ("links", "links-all"):
            print("load entities...")
            if strategy_name == "links":
                entity_db.load_entities_small(minimum_score)
            else:
                entity_db.load_entities_big()
            print(entity_db.size_entities(), "entities")
            print("load links...")
            entity_db.load_mapping()
            entity_db.load_redirects()
            entity_db.add_link_aliases()
            entity_db.load_link_frequencies()
            print(entity_db.size_aliases(), "aliases")
            strategy = LinkingStrategy.LINK_FREQUENCY
        else:
            print("load entities...")
            entity_db.load_entities_small(minimum_score)
            print(entity_db.size_entities(), "entities")
            print("add synonyms...")
            entity_db.add_synonym_aliases()
            print(entity_db.size_aliases(), "aliases")
            print("add names...")
            entity_db.add_name_aliases()
            print(entity_db.size_aliases(), "aliases")
            strategy = LinkingStrategy.ENTITY_SCORE
        linker = AliasEntityLinker(entity_db, strategy)

    file_name = sys.argv[3]
    n_examples = int(sys.argv[4])

    print("load evaluation entities...")
    entity_db = EntityDatabase()
    entity_db.load_entities_big()
    entity_db.load_mapping()
    entity_db.load_redirects()

    all_cases = []

    for i, line in enumerate(open(settings.SPLIT_ARTICLES_DIR + file_name)):
        if i == n_examples:
            break

        article = WikipediaDumpReader.json2article(line)
        if linker_type == "ambiverse":
            predictions = next(ambiverse_prediction_iterator)
        else:
            predictions = linker.predict(article.text)
        cases = []

        for span, target in article.links:
            true_entity_id = entity_db.link2id(target)

            detected = span in predictions
            if detected:
                predicted_span = span
                prediction = predictions[span]
                predicted_entity_id = prediction.entity_id
                candidates = prediction.candidates
            else:
                predicted_span = None
                predicted_entity_id = None
                candidates = set()

            case = Case(span, target, true_entity_id, predicted_span, predicted_entity_id, candidates)
            cases.append(case)

        print_str = ""
        position = 0
        for i, case in enumerate(cases):
            begin, end = case.true_span
            print_str += article.text[position:begin]
            print_str += colored(article.text[begin:end], color=case.print_color())
            position = end
        print_str += article.text[position:]
        print(print_str)
        for case in cases:
            print(colored("  %s %s (%s %s) %s %s %i" % (str(case.true_span),
                                                        article.text[case.true_span[0]:case.true_span[1]],
                                                        case.link_target,
                                                        str(case.true_entity),
                                                        str(case.predicted_span),
                                                        str(case.predicted_entity),
                                                        case.n_candidates()),
                          color=case.print_color()))
        all_cases.extend(cases)

    n_total = n_correct = n_known = n_detected = n_contained = n_is_candidate = n_true_in_multiple_candidates = \
        n_correct_multiple_candidates = 0
    for case in all_cases:
        n_total += 1
        if case.is_known_entity():
            n_known += 1
            if linker_type != "ambiverse" and linker.has_entity(case.true_entity):
                n_contained += 1
            if case.is_detected():
                n_detected += 1
                if case.true_entity_is_candidate():
                    n_is_candidate += 1
                    if len(case.candidates) > 1:
                        n_true_in_multiple_candidates += 1
                        if case.is_correct():
                            n_correct_multiple_candidates += 1
        if case.is_correct():
            n_correct += 1

    n_unknown = n_total - n_known
    n_undetected = n_known - n_detected

    print("\n== EVALUATION ==")
    print("%i links evaluated" % n_total)
    print("\t%.2f%% correct (%i/%i)" % percentage(n_correct, n_total))
    print("\t%.2f%% not a known entity (%i/%i)" % percentage(n_unknown, n_total))
    print("\t%.2f%% known entities (%i/%i)" % percentage(n_known, n_total))
    print("\t\t%.2f%% correct (%i/%i)" % percentage(n_correct, n_known))
    if linker_type != "ambiverse":
        print("\t\t%.2f%% contained (%i/%i)" % percentage(n_contained, n_known))
    print("\t\t%.2f%% not detected (%i/%i)" % percentage(n_undetected, n_known))
    print("\t\t%.2f%% detected (%i/%i)" % percentage(n_detected, n_known))
    print("\t\t\t%.2f%% correct (%i/%i)" % percentage(n_correct, n_detected))
    print("\t\t\t%.2f%% true entity in candidates (%i/%i)" % percentage(n_is_candidate, n_detected))
    print("\t\t\t\t%.2f%% correct (%i/%i)" % percentage(n_correct, n_is_candidate))
    print("\t\t\t\t%.2f%% multiple candidates (%i/%i)" % percentage(n_true_in_multiple_candidates, n_is_candidate))
    print("\t\t\t\t\t%.2f%% correct (%i/%i)" % percentage(n_correct_multiple_candidates, n_true_in_multiple_candidates))
