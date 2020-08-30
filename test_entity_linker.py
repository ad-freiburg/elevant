import time
from typing import Tuple, Optional, Set

from enum import Enum
import argparse
from termcolor import colored

from src.abstract_coref_linker import AbstractCorefLinker
from src.coreference_groundtruth_generator import CoreferenceGroundtruthGenerator
from src.entity_coref_linker import EntityCorefLinker
from src.entity_mention import EntityMention
from src.neuralcoref_coref_linker import NeuralcorefCorefLinker
from src.stanford_corenlp_coref_linker import StanfordCoreNLPCorefLinker
from src.trained_entity_linker import TrainedEntityLinker
from src.explosion_linker import ExplosionEntityLinker
from src.alias_entity_linker import AliasEntityLinker, LinkingStrategy
from src.tagme_linker import TagMeLinker
from src.entity_database import EntityDatabase
from src.ambiverse_prediction_reader import AmbiversePredictionReader
from src.conll_iob_prediction_reader import ConllIobPredictionReader
from src.evaluation_examples_generator import WikipediaExampleReader, ConllExampleReader, OwnBenchmarkExampleReader
from src.link_text_entity_linker import LinkTextEntityLinker
from src.link_entity_linker import LinkEntityLinker
from src.maximum_matching_ner import MaximumMatchingNER


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
                 candidates: Set[str],
                 predicted_by: str,
                 is_true_coref: Optional[bool] = False,
                 correct_span_referenced: Optional[bool] = False,
                 referenced_span: Optional[Tuple[int, int]] = None):
        self.span = span
        self.true_entity = true_entity
        self.detected = detected
        self.predicted_entity = predicted_entity
        self.candidates = candidates
        self.eval_type = self._type()
        self.predicted_by = predicted_by
        self.is_true_coref = is_true_coref
        self.correct_span_referenced = correct_span_referenced
        self.referenced_span = referenced_span
        self.coref_type = self._coref_type()

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

    def is_true_coreference(self):
        return self.is_true_coref

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

    def _coref_type(self) -> CaseType:
        if self.is_true_coreference():
            if not self.is_detected():
                return CaseType.UNDETECTED
            elif self.correct_span_referenced:
                return CaseType.CORRECT
            else:
                return CaseType.WRONG
        elif self.predicted_by == AbstractCorefLinker.IDENTIFIER:
            return CaseType.FALSE_DETECTION

    def __lt__(self, other):
        return self.span < other.span


def percentage(nominator: int, denominator: int) -> Tuple[float, int, int]:
    if denominator == 0:
        percent = 0
    else:
        percent = nominator / denominator * 100
    return percent, nominator, denominator


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("linker_type", choices=["baseline", "spacy", "explosion", "ambiverse", "iob", "tagme"],
                        help="Entity linker type.")
    parser.add_argument("linker",
                        help="Specify the linker to be used, depending on its type:\n"
                        "BASELINE: Choose baseline from {scores, links, links-all, max-match-ner}.\n"
                        "SPACY: Name of the linker.\n"
                        "EXPLOSION: Full path to the saved model.\n"
                        "AMBIVERSE: Full path to the predictions directory (for Wikipedia or own benchmark only).\n"
                        "IOB: Full path to the prediction file in IOB format (for CoNLL benchmark only).\n")
    parser.add_argument("-b", "--benchmark", choices=["own", "wikipedia", "conll"], default="own",
                        help="Benchmark over which to evaluate the linker.")
    parser.add_argument("-n", "--n_articles", type=int, default=-1,
                        help="Number of articles to evaluate on.")
    parser.add_argument("-kb", "--kb_name", type=str, choices=["wikipedia"], default=None,
                        help="Name of the knowledge base to use with a spacy linker.")
    parser.add_argument("-ll", "--link_linker", choices=["link-linker", "link-text-linker"], default=None,
                        help="Link linker to apply before spacy or explosion linker")
    parser.add_argument("-coref", "--coreference_linker", choices=["neuralcoref", "entity", "stanford"], default=None,
                        help="Coreference linker to apply after entity linkers.")
    parser.add_argument("--evaluation_span", action="store_true",
                        help="If specified, let coreference linker refer only to entities within the evaluation span")
    parser.add_argument("-min", "--minimum_score", type=int, default=0,
                        help="Minimum entity score to include entity in database")
    parser.add_argument("-small", "--small_database", action="store_true",
                        help="Load a small version of the database")
    parser.add_argument("--no_coreference", action="store_true",
                        help="Exclude coreference cases from the evalutation.")
    args = parser.parse_args()

    if args.link_linker:
        if args.linker_type not in {"spacy", "explosion"}:
            print("Link linkers can only be applied for spacy or explosion linker.")
            exit(1)
        elif args.benchmark != "own":
            print("Link linkers can only be evaluated over own benchmark.")
            exit(1)

    print("load entities...")
    entity_db = EntityDatabase()
    if (args.linker_type == "baseline" and args.linker == "max-match-ner")\
            or args.linker_type == "tagme":
        pass
    elif args.linker_type == "baseline" and args.linker in ("scores", "links"):
        entity_db.load_entities_small(args.minimum_score)
    else:
        entity_db.load_entities_big()
    print(entity_db.size_entities(), "entities")
    if args.linker_type == "baseline":
        if args.linker == "max-match-ner":
            pass
        elif args.linker in ("links", "links-all"):
            print("load link frequencies...")
            entity_db.load_mapping()
            entity_db.load_redirects()
            entity_db.add_link_aliases()
            entity_db.load_link_frequencies()
        else:
            print("add synonyms...")
            entity_db.add_synonym_aliases()
            print(entity_db.size_aliases(), "aliases")
            print("add names...")
            entity_db.add_name_aliases()
            print(entity_db.size_aliases(), "aliases")
        if args.link_linker:
            print("add redirects...")
            entity_db.load_redirects()
            print("add synonyms...")
            entity_db.add_synonym_aliases()
            print(entity_db.size_aliases(), "aliases")
            print("add names...")
            entity_db.add_name_aliases()
            print(entity_db.size_aliases(), "aliases")
            print("add link aliases")
            entity_db.add_link_aliases()
            print(entity_db.size_aliases(), "aliases")

    linker = None
    prediction_iterator = None
    if args.linker_type == "spacy":
        linker_name = args.linker
        linker = TrainedEntityLinker(linker_name, entity_db=entity_db, kb_name=args.kb_name)
    elif args.linker_type == "explosion":
        path = args.linker
        linker = ExplosionEntityLinker(path, entity_db=entity_db)
    elif args.linker_type == "iob":
        path = args.linker
        prediction_iterator = ConllIobPredictionReader.document_predictions_iterator(path)
    elif args.linker_type == "ambiverse":
        result_dir = args.linker
        prediction_iterator = AmbiversePredictionReader.article_predictions_iterator(result_dir)
    elif args.linker_type == "tagme":
        rho_threshold = float(args.linker)
        linker = TagMeLinker(rho_threshold)
    else:
        if args.linker == "max-match-ner":
            linker = MaximumMatchingNER()
        else:
            if args.linker not in ("links", "scores", "links-all"):
                raise NotImplementedError("Unknown strategy '%s'." % args.linker)
            if args.linker in ("links", "links-all"):
                strategy = LinkingStrategy.LINK_FREQUENCY
            else:
                strategy = LinkingStrategy.ENTITY_SCORE
            linker = AliasEntityLinker(entity_db, strategy)

    print("load evaluation entities...")
    entity_db = EntityDatabase()
    entity_db.load_entities_small() if args.small_database else entity_db.load_entities_big()
    entity_db.load_mapping()
    entity_db.load_redirects()

    COREFERENCE_PRONOUNS = {"he", "she", "it", "his", "her", "its", "him", "they", "their", "theirs"}

    link_linker = None
    if args.link_linker == "link-text-linker":
        link_linker = LinkTextEntityLinker(entity_db=entity_db)
    elif args.link_linker == "link-linker":
        link_linker = LinkEntityLinker()

    coreference_linker = None
    if args.coreference_linker and not args.evaluation_span:
        print("Warning: For a proper coreference evaluation add option --evaluation_span")
        print("\tOtherwise referenced entities can occur outside of the evaluation span.")
        print("\tThis can however lead to different overall results.")
    if args.coreference_linker == "neuralcoref":
        coreference_linker = NeuralcorefCorefLinker()
    elif args.coreference_linker == "entity":
        print("load gender information...")
        entity_db.load_gender()
        coreference_linker = EntityCorefLinker(entity_db=entity_db)
    elif args.coreference_linker == "stanford":
        coreference_linker = StanfordCoreNLPCorefLinker()

    if args.benchmark == "conll":
        example_generator = ConllExampleReader(entity_db)
    elif args.benchmark == "own":
        example_generator = OwnBenchmarkExampleReader()
    else:
        example_generator = WikipediaExampleReader(entity_db)

    coref_groundtruth_generator = CoreferenceGroundtruthGenerator()

    all_cases = []
    n_ner_tp = n_ner_fp = n_ner_fn = 0

    start_time = time.time()
    for article, ground_truth, evaluation_span in example_generator.iterate(args.n_articles):
        text = article.text

        if args.no_coreference:
            filtered_ground_truth = set()
            for span, entity_id in ground_truth:
                snippet = text[span[0]:span[1]]
                if snippet.lower() not in COREFERENCE_PRONOUNS and not snippet.startswith("the "):
                    filtered_ground_truth.add((span, entity_id))
            ground_truth = filtered_ground_truth

        if linker is None:
            predictions = next(prediction_iterator)
            coref_groundtruth = coref_groundtruth_generator.get_groundtruth(article)
        else:
            if linker.model:
                doc = linker.model(text)
            else:
                doc = None

            if args.link_linker:
                link_linker.link_entities(article)

            predictions = {}
            if not args.link_linker and not args.coreference_linker:
                linker_predictions = linker.predict(text, doc)
                for span, ep in linker_predictions.items():
                    entity_mention = EntityMention(span,
                                                   recognized_by=linker.NER_IDENTIFIER,
                                                   entity_id=ep.entity_id,
                                                   linked_by=linker.LINKER_IDENTIFIER)
                    predictions[span] = entity_mention, ep.candidates
            else:
                linker.link_entities(article, doc)

            coref_groundtruth = coref_groundtruth_generator.get_groundtruth(article, doc)
            if args.coreference_linker:
                if args.evaluation_span:
                    coreference_linker.link_entities(article, only_pronouns=True, evaluation_span=evaluation_span)
                else:
                    coreference_linker.link_entities(article, only_pronouns=True)

            if args.link_linker or args.coreference_linker:
                for em in article.entity_mentions.values():
                    predictions[em.span] = em, {em.entity_id}

        ground_truth_spans = set(span for span, _ in ground_truth)
        cases = []

        # ground truth cases:
        for span, true_entity_id in sorted(ground_truth):
            detected = span in predictions
            predicted_mention = None
            if detected:
                predicted_mention, candidates = predictions[span]
                predicted_by = predicted_mention.linked_by
                predicted_entity_id = predicted_mention.entity_id
            else:
                predicted_by = None
                predicted_entity_id = None
                candidates = set()

            referenced_span = None
            is_true_coref = span in coref_groundtruth
            correct_span_referenced = False
            if detected and predicted_by == AbstractCorefLinker.IDENTIFIER:
                referenced_span = predicted_mention.referenced_span
                if is_true_coref:
                    for poss_ref_span in coref_groundtruth[span]:
                        # Do not require a perfect match of the spans but look for overlaps
                        if poss_ref_span[0] <= referenced_span[1] <= poss_ref_span[1] or \
                                poss_ref_span[0] <= referenced_span[0] <= poss_ref_span[1]:
                            correct_span_referenced = True
                            break

            case = Case(span, true_entity_id, detected, predicted_entity_id, candidates, predicted_by,
                        is_true_coref=is_true_coref,
                        correct_span_referenced=correct_span_referenced,
                        referenced_span=referenced_span)
            cases.append(case)

        # predicted cases (potential false detections):
        for span in predictions:
            predicted_mention, candidates = predictions[span]
            predicted_entity_id = predicted_mention.entity_id
            if span not in ground_truth_spans and predicted_entity_id is not None and span[0] >= evaluation_span[0] \
                    and span[1] <= evaluation_span[1]:
                predicted_by = predicted_mention.linked_by
                case = Case(span, None, True, predicted_entity_id, candidates=candidates,
                            predicted_by=predicted_by, referenced_span=predicted_mention.referenced_span)
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

        # NER evaluation:
        predicted_spans = set(predictions)
        if args.evaluation_span:
            eval_begin, eval_end = evaluation_span
            predicted_spans = {(begin, end) for begin, end in predicted_spans
                               if begin >= eval_begin and end <= eval_end}
        ner_tp = ground_truth_spans.intersection(predicted_spans)
        ner_fp = predicted_spans.difference(ground_truth_spans)
        ner_fn = ground_truth_spans.difference(predicted_spans)
        n_ner_tp += len(ner_tp)
        n_ner_fp += len(ner_fp)
        n_ner_fn += len(ner_fn)
        print("NER TP:", [(span, text[span[0]:span[1]]) for span in ner_tp])
        print("NER FP:", [(span, text[span[0]:span[1]]) for span in ner_fp])
        print("NER FN:", [(span, text[span[0]:span[1]]) for span in ner_fn])

        for case in cases:
            true_str = "(%s %s)" % (case.true_entity, entity_db.get_entity(case.true_entity).name
                                    if entity_db.contains_entity(case.true_entity) else "Unknown") \
                if case.true_entity is not None else "None"
            referenced_span = " -> %s" % (str(case.referenced_span)) \
                if case.predicted_by == AbstractCorefLinker.IDENTIFIER else ""
            predicted_str = "(%s %s [%s]%s)" % (case.predicted_entity,
                                                entity_db.get_entity(case.predicted_entity).name
                                                if entity_db.contains_entity(case.predicted_entity) else "Unknown",
                                                case.predicted_by, referenced_span) \
                if case.predicted_entity is not None else "None"
            print(colored("  %s %s %s %s %i %s" % (str(case.span),
                                                   text[case.span[0]:case.span[1]],
                                                   true_str,
                                                   predicted_str,
                                                   case.n_candidates(),
                                                   case.eval_type.name),
                          color=CASE_COLORS[case.eval_type]))

        coref_cases = [c for c in cases
                       if c.is_true_coreference() or c.predicted_by == AbstractCorefLinker.IDENTIFIER]
        if coref_cases:
            print()
            print("Coreference Cases:")
            for case in coref_cases:
                true_str = "(%s %s)" % (case.true_entity, entity_db.get_entity(case.true_entity).name
                                        if entity_db.contains_entity(case.true_entity) else "Unknown") \
                    if case.true_entity is not None else "None"
                referenced_span = " -> %s %s" % (str(case.referenced_span), text[case.referenced_span[0]:
                                                                                 case.referenced_span[1]])\
                    if case.predicted_by == AbstractCorefLinker.IDENTIFIER else ""
                predicted_str = "(%s %s %s)" % (case.predicted_entity,
                                                entity_db.get_entity(case.predicted_entity).name
                                                if entity_db.contains_entity(case.predicted_entity) else "Unknown",
                                                referenced_span) \
                    if case.predicted_entity is not None else "None"
                print(colored("  %s %s %s %s %i %s" % (str(case.span),
                                                       text[case.span[0]:case.span[1]],
                                                       true_str,
                                                       predicted_str,
                                                       case.n_candidates(),
                                                       case.coref_type.name),
                              color=CASE_COLORS[case.coref_type]))

        all_cases.extend(cases)

    total_time = time.time() - start_time

    n_total = n_correct = n_known = n_detected = n_contained = n_is_candidate = n_true_in_multiple_candidates = \
        n_correct_multiple_candidates = n_false_positives = n_false_negatives = n_ground_truth = n_false_detection = \
        n_coref_total = n_coref_tp = n_coref_fp = 0
    for case in all_cases:
        n_total += 1

        if case.is_true_coreference():
            n_coref_total += 1
            if case.correct_span_referenced:
                n_coref_tp += 1
            else:
                n_coref_fp += 1
        if case.predicted_by == AbstractCorefLinker.IDENTIFIER:
            if not case.is_true_coreference():
                n_coref_fp += 1

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
        elif case.is_known_entity():
            n_false_negatives += 1
        if case.is_false_positive():
            n_false_positives += 1
        if case.eval_type == CaseType.FALSE_DETECTION:
            n_false_detection += 1

    n_unknown = n_ground_truth - n_known
    n_undetected = n_known - n_detected

    print("\n== EVALUATION ==")
    print("%i ground truth entity mentions evaluated" % n_ground_truth)
    print("\t%.2f%% correct (%i/%i)" % percentage(n_correct, n_ground_truth))
    print("\t%.2f%% not a known entity (%i/%i)" % percentage(n_unknown, n_ground_truth))
    print("\t%.2f%% known entities (%i/%i)" % percentage(n_known, n_ground_truth))
    print("\t\t%.2f%% correct (%i/%i)" % percentage(n_correct, n_known))
    if args.linker_type != "ambiverse":
        print("\t\t%.2f%% contained (%i/%i)" % percentage(n_contained, n_known))
    print("\t\t%.2f%% not detected (%i/%i)" % percentage(n_undetected, n_known))
    print("\t\t%.2f%% detected (%i/%i)" % percentage(n_detected, n_known))
    print("\t\t\t%.2f%% correct (%i/%i)" % percentage(n_correct, n_detected))
    # Link-linker and coreference-linker do not yield candidate information
    if not args.link_linker and not args.coreference_linker:
        print("\t\t\t%.2f%% true entity in candidates (%i/%i)" % percentage(n_is_candidate, n_detected))
        print("\t\t\t\t%.2f%% correct (%i/%i)" % percentage(n_correct, n_is_candidate))
        print("\t\t\t\t%.2f%% multiple candidates (%i/%i)" % percentage(n_true_in_multiple_candidates, n_is_candidate))
        print("\t\t\t\t\t%.2f%% correct (%i/%i)" % percentage(n_correct_multiple_candidates,
                                                              n_true_in_multiple_candidates))
    if args.coreference_linker:
        print()
        print("Coreference evaluation:")
        print("\tprecision = %.2f%% (%i/%i)" % percentage(n_coref_tp, n_coref_tp + n_coref_fp))
        print("\trecall =    %.2f%% (%i/%i)" % percentage(n_coref_tp, n_coref_total))
        precision = n_coref_tp / (n_coref_tp + n_coref_fp)
        recall = n_coref_tp / n_coref_total
        f1 = 2 * precision * recall / (precision + recall)
        print("\tf1 =        %.2f%%" % (f1*100))

    print("\nNER:")
    ner_precision, ner_prec_nominator, ner_prec_denominator = percentage(n_ner_tp, n_ner_tp + n_ner_fp)
    print("precision = %.2f%% (%i/%i)" % (ner_precision, ner_prec_nominator, ner_prec_denominator))
    ner_recall, ner_rec_nominator, ner_rec_denominator = percentage(n_ner_tp, n_ner_tp + n_ner_fn)
    print("recall =    %.2f%% (%i/%i)" % (ner_recall, ner_rec_nominator, ner_rec_denominator))
    ner_precision = ner_precision / 100
    ner_recall = ner_recall / 100
    ner_f1 = 2 * ner_precision * ner_recall / (ner_precision + ner_recall)
    print("f1 =        %.2f%%" % (ner_f1 * 100))

    print("\nNERD:")
    print("tp = %i, fp = %i (false detections = %i), fn = %i" %
          (n_correct, n_false_positives, n_false_detection, n_false_negatives))
    precision, prec_nominator, prec_denominator = percentage(n_correct, n_correct + n_false_positives)
    print("precision = %.2f%% (%i/%i)" % (precision, prec_nominator, prec_denominator))
    recall, rec_nominator, rec_denominator = percentage(n_correct, n_correct + n_false_negatives)
    print("recall =    %.2f%% (%i/%i)" % (recall, rec_nominator, rec_denominator))
    precision = precision / 100
    recall = recall / 100
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    print("f1 =        %.2f%%" % (f1 * 100))

    print("\nEvaluation done in %.2fs" % total_time)
