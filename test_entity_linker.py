from typing import Tuple, Optional, Set

from enum import Enum
import sys
from termcolor import colored

from src.trained_entity_linker import TrainedEntityLinker
from src.explosion_linker import ExplosionEntityLinker
from src.alias_entity_linker import AliasEntityLinker, LinkingStrategy
from src.entity_database_new import EntityDatabase
from src.ambiverse_prediction_reader import AmbiversePredictionReader
from src.conll_iob_prediction_reader import ConllIobPredictionReader
from src.evaluation_examples_generator import WikipediaExampleReader, ConllExampleReader


class CaseType(Enum):
    UNKNOWN_ENTITY = 0
    UNDETECTED = 1
    WRONG_CANDIDATES = 2
    CORRECT = 3
    WRONG = 4
    FALSE_DETECTION = 5


CASE_COLORS = {
    CaseType.UNKNOWN_ENTITY: None,
    CaseType.UNDETECTED: "blue",
    CaseType.WRONG_CANDIDATES: "yellow",
    CaseType.CORRECT: "green",
    CaseType.WRONG: "red",
    CaseType.FALSE_DETECTION: "cyan",
    "mixed": "magenta"
}


class Case:
    def __init__(self,
                 span: Tuple[int, int],
                 true_entity: Optional[str],
                 detected: bool,
                 predicted_entity: Optional[str],
                 candidates: Set[str]):
        self.span = span
        self.true_entity = true_entity
        self.detected = detected
        self.predicted_entity = predicted_entity
        self.candidates = candidates
        self.eval_type = self._type()

    def has_ground_truth(self):
        return self.true_entity is not None

    def is_known_entity(self):
        return self.true_entity is not None and self.true_entity != "Unknown"

    def is_detected(self):
        return self.detected

    def is_correct(self):
        return self.predicted_entity is not None and self.true_entity == self.predicted_entity

    def true_entity_is_candidate(self):
        return self.true_entity in self.candidates

    def n_candidates(self):
        return len(self.candidates)

    def is_false_positive(self):
        return self.predicted_entity is not None and self.true_entity != self.predicted_entity

    def _type(self) -> CaseType:
        if not self.has_ground_truth():
            return CaseType.FALSE_DETECTION
        if not self.is_known_entity():
            return CaseType.UNKNOWN_ENTITY
        if not self.is_detected():
            return CaseType.UNDETECTED
        if not self.true_entity_is_candidate():
            return CaseType.WRONG_CANDIDATES
        if self.is_correct():
            return CaseType.CORRECT
        else:
            return CaseType.WRONG

    def __lt__(self, other):
        return self.span < other.span


def percentage(nominator: int, denominator: int) -> Tuple[float, int, int]:
    if denominator == 0:
        percent = 0
    else:
        percent = nominator / denominator * 100
    return percent, nominator, denominator


def print_help():
    print("Usage:\n"
          "    python3 <linker_type> <linker> <benchmark> <n_articles>\n"
          "\n"
          "Arguments:\n"
          "    <linker_type>: Choose from {baseline, spacy, explosion, iob}.\n"
          "    <linker>: Specify the linker to be used, depending on its type:\n"
          "        baseline: Choose baseline from {scores, links, links-all}.\n"
          "        spacy: Name of the linker.\n"
          "        explosion: Full path to the saved model.\n"
          "        iob: Full path to the prediction file in IOB format (for the CoNLL benchmark only).\n"
          "    <benchmark>: Choose from {wikipedia, conll}.\n"
          "    <n_articles>: Number of articles to evaluate on.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_help()
        exit(1)

    linker_type = sys.argv[1]
    if linker_type not in ("spacy", "explosion", "ambiverse", "baseline", "iob"):
        raise NotImplementedError("Unknown linker type '%s'." % linker_type)

    linker = None
    if linker_type == "spacy":
        linker_name = sys.argv[2]
        linker = TrainedEntityLinker(linker_name)
    elif linker_type == "explosion":
        path = sys.argv[2]
        linker = ExplosionEntityLinker(path)
    elif linker_type == "iob":
        path = sys.argv[2]
        prediction_iterator = ConllIobPredictionReader.document_predictions_iterator(path)
    elif linker_type == "ambiverse":
        result_dir = sys.argv[2]
        prediction_iterator = AmbiversePredictionReader.article_predictions_iterator(result_dir)
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

    if file_name == "conll":
        example_generator = ConllExampleReader(entity_db)
    else:
        example_generator = WikipediaExampleReader(entity_db)

    all_cases = []

    for text, ground_truth in example_generator.iterate(n_examples):
        if linker is None:
            predictions = next(prediction_iterator)
        else:
            predictions = linker.predict(text)

        cases = []

        # ground truth cases:
        for span, true_entity_id in sorted(ground_truth):
            detected = span in predictions
            if detected:
                prediction = predictions[span]
                predicted_entity_id = prediction.entity_id
                candidates = prediction.candidates
            else:
                predicted_entity_id = None
                candidates = set()

            case = Case(span, true_entity_id, detected, predicted_entity_id, candidates)
            cases.append(case)

        # predicted cases (potential false detections):
        ground_truth_spans = set(span for span, _ in ground_truth)
        for span in predictions:
            predicted_entity_id = predictions[span].entity_id
            if span not in ground_truth_spans and predicted_entity_id is not None:
                case = Case(span, None, True, predicted_entity_id, candidates=predictions[span].candidates)
                cases.append(case)

        cases = sorted(cases)

        colored_spans = [(case.span, CASE_COLORS[case.eval_type]) for case in cases
                         if case.eval_type != CaseType.UNKNOWN_ENTITY]
        i = 0
        while i + 1 < len(colored_spans):
            span, color = colored_spans[i]
            next_span, next_color = colored_spans[i + 1]
            if span[1] > next_span[0]:
                left_span = (span[0], next_span[0]), color
                mid_span = (next_span[0], span[1]), CASE_COLORS["mixed"]
                right_span = (span[1], next_span[1]), next_color
                colored_spans = colored_spans[:i] + [left_span, mid_span, right_span] + colored_spans[(i + 2):]
            i += 1

        print_str = ""
        position = 0
        for span, color in colored_spans:
            begin, end = span
            print_str += text[position:begin]
            print_str += colored(text[begin:end], color=color)
            position = end
        print_str += text[position:]
        print(print_str)

        for case in cases:
            true_str = "(%s %s)" % (case.true_entity, entity_db.get_entity(case.true_entity).name
                                    if entity_db.contains_entity(case.true_entity) else "Unknown") \
                if case.true_entity is not None else "None"
            predicted_str = "(%s %s)" % (case.predicted_entity,
                                         entity_db.get_entity(case.predicted_entity).name
                                         if entity_db.contains_entity(case.predicted_entity) else "Unknown") \
                if case.predicted_entity is not None else "None"
            print(colored("  %s %s %s %s %i %s" % (str(case.span),
                                                   text[case.span[0]:case.span[1]],
                                                   true_str,
                                                   predicted_str,
                                                   case.n_candidates(),
                                                   case.eval_type.name),
                          color=CASE_COLORS[case.eval_type]))
        all_cases.extend(cases)

    n_total = n_correct = n_known = n_detected = n_contained = n_is_candidate = n_true_in_multiple_candidates = \
        n_correct_multiple_candidates = n_false_positives = n_false_negatives = n_ground_truth = 0
    for case in all_cases:
        n_total += 1
        if case.has_ground_truth():
            n_ground_truth += 1
            if case.is_known_entity():
                n_known += 1
                if linker is not None and linker.has_entity(case.true_entity):
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
        elif case.has_ground_truth():
            n_false_negatives += 1
        if case.is_false_positive():
            n_false_positives += 1

    n_unknown = n_ground_truth - n_known
    n_undetected = n_known - n_detected

    print("\n== EVALUATION ==")
    print("%i ground truth entity mentions evaluated" % n_ground_truth)
    print("\t%.2f%% correct (%i/%i)" % percentage(n_correct, n_ground_truth))
    print("\t%.2f%% not a known entity (%i/%i)" % percentage(n_unknown, n_ground_truth))
    print("\t%.2f%% known entities (%i/%i)" % percentage(n_known, n_ground_truth))
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
    print("precision = %.2f%% (%i/%i)" % percentage(n_correct, n_correct + n_false_positives))
    print("recall =    %.2f%% (%i/%i)" % percentage(n_correct, n_correct + n_false_negatives))
    precision = n_correct / (n_correct + n_false_positives)
    recall = n_correct / (n_correct + n_false_negatives)
    f1 = 2 * precision * recall / (precision + recall)
    print("f1 =        %.2f%%" % (f1 * 100))
