from typing import Tuple, Optional

import sys
from enum import Enum
from termcolor import colored

from src.trained_entity_linker import TrainedEntityLinker
from src.alias_entity_linker import AliasEntityLinker
from src.paragraph_reader import ParagraphReader
from src.link_entity_linker import LinkEntityLinker


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
                 true_entity: str,
                 predicted_span: Tuple[int, int],
                 predicted_entity: Optional[str],
                 n_candidates: int,
                 case_type: CaseType):
        self.true_span = true_span
        self.true_entity = true_entity
        self.predicted_span = predicted_span
        self.predicted_entity = predicted_entity
        self.n_candidates = n_candidates
        self.case_type = case_type

    def is_correct(self):
        return self.case_type.is_correct()


def print_help():
    print("Usage:\n"
          "    python3 test_entity_linker.py <linker> <n_paragraphs>")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print_help()
        exit(1)

    linker_name = sys.argv[1]
    n_examples = int(sys.argv[2])

    if linker_name == "trained":
        linker = TrainedEntityLinker()
    elif linker_name == "links":
        linker = AliasEntityLinker()
    else:
        raise Exception("Unknown linker '%s'." % linker_name)

    wikipedia2wikidata_linker = LinkEntityLinker()
    case_counter = {case_type: 0 for case_type in CaseType}

    for p_i, paragraph in enumerate(ParagraphReader.development_paragraphs()):
        if p_i == n_examples:
            break

        predictions = linker.predict(paragraph.text)
        cases = []

        for span, target in paragraph.wikipedia_links:
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
            case_counter[case] += 1
            case = Case(span, true_entity_id, span, predicted_entity_id, n_candidates, case)
            cases.append(case)

        print_str = ""
        position = 0
        for i, case in enumerate(cases):
            begin, end = case.predicted_span
            print_str += paragraph.text[position:begin]
            print_str += colored(paragraph.text[begin:end], color=CASE_COLORS[case.case_type])
            position = end
        print_str += paragraph.text[position:]
        print(print_str)
        for case in cases:
            print(colored("  %s %s %s %s %s %i" % (str(case.true_span),
                                                   str(case.true_entity),
                                                   str(case.predicted_span),
                                                   str(case.predicted_entity),
                                                   case.case_type.name,
                                                   case.n_candidates),
                          color=CASE_COLORS[case.case_type]))

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
