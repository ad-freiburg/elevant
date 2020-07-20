from typing import Tuple, Optional

import sys
from enum import Enum
from termcolor import colored

from src.trained_entity_linker import TrainedEntityLinker
from src.alias_entity_linker import AliasEntityLinker, LinkingStrategy
from src.link_entity_linker import LinkEntityLinker
from src.entity_database_reader import EntityDatabaseReader
from src.wikipedia_dump_reader import WikipediaDumpReader
from src.ambiverse_prediction_reader import AmbiversePredictionReader
from src import settings


class CaseType(Enum):
    UNDETECTED = 1
    UNKNOWN = 2
    NO_CANDIDATE = 3
    SINGLE_CANDIDATE_CORRECT = 4
    SINGLE_CANDIDATE_WRONG = 5
    MULTI_CANDIDATE_CORRECT = 6
    MULTI_CANDIDATE_ALL_WRONG = 7
    MULTI_CANDIDATE_WRONG = 8

    def is_correct(self):
        return self == CaseType.SINGLE_CANDIDATE_CORRECT or self == CaseType.MULTI_CANDIDATE_CORRECT


CASE_COLORS = {
    CaseType.UNDETECTED: "blue",
    CaseType.UNKNOWN: "yellow",
    CaseType.NO_CANDIDATE: "red",
    CaseType.SINGLE_CANDIDATE_CORRECT: "green",
    CaseType.SINGLE_CANDIDATE_WRONG: "red",
    CaseType.MULTI_CANDIDATE_CORRECT: "green",
    CaseType.MULTI_CANDIDATE_ALL_WRONG: "red",
    CaseType.MULTI_CANDIDATE_WRONG: "red"
}


class Case:
    def __init__(self,
                 true_span: Tuple[int, int],
                 link_target: str,
                 true_entity: str,
                 predicted_span: Tuple[int, int],
                 predicted_entity: Optional[str],
                 n_candidates: int,
                 case_type: CaseType):
        self.true_span = true_span
        self.link_target = link_target
        self.true_entity = true_entity
        self.predicted_span = predicted_span
        self.predicted_entity = predicted_entity
        self.n_candidates = n_candidates
        self.case_type = case_type

    def is_correct(self):
        return self.case_type.is_correct()


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
          "        links:   Baseline using link frequencies for disambiguation.\n"
          "        scores:  Baseline using entity scores for disambiguation.\n"
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
        if strategy_name not in ("links", "scores"):
            raise NotImplementedError("Unknown strategy '%s'." % strategy_name)
        if strategy_name == "links":
            strategy = LinkingStrategy.LINK_FREQUENCY
        else:
            strategy = LinkingStrategy.ENTITY_SCORE
        minimum_score = int(sys.argv[5]) if len(sys.argv) > 5 else 0
        entity_db = EntityDatabaseReader.read_entity_database(minimum_score=minimum_score)
        linker = AliasEntityLinker(entity_db, strategy)

    file_name = sys.argv[3]
    n_examples = int(sys.argv[4])

    wikipedia2wikidata_linker = LinkEntityLinker()
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
            if wikipedia2wikidata_linker.contains_name(target):
                true_entity_id = wikipedia2wikidata_linker.get_entity_id(target)
            else:
                true_entity_id = None

            detected = span in predictions
            if detected:
                prediction = predictions[span]
                predicted_entity_id = prediction.entity_id
                candidates = prediction.candidates
            else:
                predicted_entity_id = None
                candidates = set()
            n_candidates = len(candidates)

            if true_entity_id is None:
                case = CaseType.UNKNOWN
            elif not detected:
                case = CaseType.UNDETECTED
            else:
                is_correct = (true_entity_id == predicted_entity_id)
                if n_candidates == 0:
                    case = CaseType.NO_CANDIDATE
                elif n_candidates == 1:
                    if is_correct:
                        case = CaseType.SINGLE_CANDIDATE_CORRECT
                    else:
                        case = CaseType.SINGLE_CANDIDATE_WRONG
                else:
                    if true_entity_id in candidates:
                        if is_correct:
                            case = CaseType.MULTI_CANDIDATE_CORRECT
                        else:
                            case = CaseType.MULTI_CANDIDATE_WRONG
                    else:
                        case = CaseType.MULTI_CANDIDATE_ALL_WRONG
            case = Case(span, target, true_entity_id, span, predicted_entity_id, n_candidates, case)
            cases.append(case)

        print_str = ""
        position = 0
        for i, case in enumerate(cases):
            begin, end = case.predicted_span
            print_str += article.text[position:begin]
            print_str += colored(article.text[begin:end], color=CASE_COLORS[case.case_type])
            position = end
        print_str += article.text[position:]
        print(print_str)
        for case in cases:
            print(colored("  %s %s (%s %s) %s %s %s %i" % (str(case.true_span),
                                                           article.text[case.true_span[0]:case.true_span[1]],
                                                           case.link_target,
                                                           str(case.true_entity),
                                                           str(case.predicted_span),
                                                           str(case.predicted_entity),
                                                           case.case_type.name,
                                                           case.n_candidates),
                          color=CASE_COLORS[case.case_type]))
        all_cases.extend(cases)

    case_counter = {case_type: 0 for case_type in CaseType}
    for case in all_cases:
        case_counter[case.case_type] += 1

    print("\n== EVALUATION ==")
    n_total = sum(case_counter[case_type] for case_type in CaseType)
    print("%i links evaluated" % n_total)
    n_correct = sum(case_counter[case_type] for case_type in CaseType if case_type.is_correct())
    print("\t%.2f%% correct (%i/%i)" % (n_correct / n_total * 100, n_correct, n_total))
    n_unknown = case_counter[CaseType.UNKNOWN]
    print("\t%.2f%% not a known entity (%i/%i)" % (n_unknown / n_total * 100, n_unknown, n_total))
    n_known = n_total - n_unknown
    print("\t%.2f%% known entities (%i/%i)" % (n_known / n_total * 100, n_known, n_total))
    print("\t\t%.2f%% correct (%i/%i)" % (n_correct / n_known * 100, n_correct, n_known))
    n_undetected = case_counter[CaseType.UNDETECTED]
    if linker_type != "ambiverse":
        n_contained = len([case for case in all_cases if linker.has_entity(case.true_entity)])
        print("\t\t%.2f%% contained (%i/%i)" % (n_contained / n_known * 100, n_contained, n_known))
    print("\t\t%.2f%% not detected (%i/%i)" % (n_undetected / n_known * 100, n_undetected, n_known))
    n_detected = n_known - n_undetected
    print("\t\t%.2f%% detected (%i/%i)" % (n_detected / n_known * 100, n_detected, n_known))
    print("\t\t\t%.2f%% correct (%i/%i)" % (n_correct / n_detected * 100, n_correct, n_detected))
    n_no_candidate = case_counter[CaseType.NO_CANDIDATE]
    print("\t\t\t%.2f%% no candidate (%i/%i)" % (n_no_candidate / n_detected * 100, n_no_candidate, n_detected))
    n_single_candidate = case_counter[CaseType.SINGLE_CANDIDATE_WRONG] + case_counter[CaseType.SINGLE_CANDIDATE_CORRECT]
    print("\t\t\t%.2f%% 1 candidate (%i/%i)" % (n_single_candidate / n_detected * 100, n_single_candidate, n_detected))
    n_single_candidate_correct = case_counter[CaseType.SINGLE_CANDIDATE_CORRECT]
    print("\t\t\t\t%.2f%% correct (%i/%i)" % (n_single_candidate_correct / n_single_candidate * 100,
                                              n_single_candidate_correct, n_single_candidate))
    n_multi_candidates = case_counter[CaseType.MULTI_CANDIDATE_ALL_WRONG] + \
        case_counter[CaseType.MULTI_CANDIDATE_WRONG] + case_counter[CaseType.MULTI_CANDIDATE_CORRECT]
    print("\t\t\t%.2f%% >1 candidate (%i/%i)" % (n_multi_candidates / n_detected * 100, n_multi_candidates, n_detected))
    n_multi_candidates_correct = case_counter[CaseType.MULTI_CANDIDATE_CORRECT]
    print("\t\t\t\t%.2f%% correct (%i/%i)" % (n_multi_candidates_correct / n_multi_candidates * 100,
                                              n_multi_candidates_correct, n_multi_candidates))
    n_multi_candidates_all_wrong = case_counter[CaseType.MULTI_CANDIDATE_ALL_WRONG]
    print("\t\t\t\t%.2f%% wrong candidates (%i/%i)" % (n_multi_candidates_all_wrong / n_multi_candidates * 100,
                                                       n_multi_candidates_all_wrong, n_multi_candidates))
    n_multi_candidates_right_contained = n_multi_candidates - n_multi_candidates_all_wrong
    print("\t\t\t\t%.2f%% right contained (%i/%i)" % (n_multi_candidates_right_contained / n_multi_candidates * 100,
                                                      n_multi_candidates_right_contained, n_multi_candidates))
    print("\t\t\t\t\t%.2f%% correct (%i/%i)" % (n_multi_candidates_correct / n_multi_candidates_right_contained * 100,
                                                n_multi_candidates_correct, n_multi_candidates_right_contained))
