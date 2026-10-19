import os, json, time
from urllib.request import Request, urlopen
from typing import Optional, Any
from concurrent.futures import ThreadPoolExecutor
from elevant.models.entity_database import EntityDatabase
from elevant.models.entity_prediction import EntityPrediction
from elevant.linkers.abstract_entity_linker import AbstractEntityLinker


# These are simple instructions that seem to work for KORE50 and AIDA-CoNLL
named_instructions = """Link only named entities.
Link metonyms with their intended meaning that is maybe only obvious from the context.
If you cannot find an entity for the intended meaning, link it with the literal meaning."""


# These are the shortened instructions for the Wiki-Fair and News-Fair benchmarks 
# given in the paper excluding the sections on coreference, NIL, quantity, datetime
fair_instructions = """## Annotation guidelines
**What to annotate:**
Only annotate entities that
are an instance of at least one of our whitelist types
or an instance of a subclass of one of the whitelist
types.

**Demonyms:**
In general, annotate demonym men-
tions with the country. Additionally, annotate the
mention with the ethnicity or country-citizens if
the culture or ethnicity is being referred to (e.g.,
"[American] dish"). The mention should not be
annotated with the ethnicity in cases like "[Soviet]-
backed United Arab Republic" (Soviet refers to (a
part of) the government which is better represented
by the country) or "[American] movie" (it's still an
American movie if the director decides to migrate
to another country). Only annotate the mention
with the language if it is obvious that the language
is being referred to (e.g., 'sectores" means "sec-
tors" in [Spanish]'.

**Type Whitelist**
Person (Q215627), Fictional Character
(Q95074), Geographic Entity (Q27096213),
Fictional Location (Q3895768), Organization
(Q43229), Creative Work (Q17537576), Product
(Q2424752), Event (Q1656682), Brand (Q431289),
Genre (Q483394), Languoid (Q17376908), Chemi-
cal Entity (Q43460564), Taxon (Q16521), Religion
(Q9174), Ideology (Q7257), Position (Q4164871),
Occupation (Q12737077), Academic Discipline
(Q11862829), Narrative Entity (Q21070598),
Award (Q618779), Disease (Q12136), Religious
Identity (Q4392985), Record Chart (Q373899),
Government Program (Q22222786), Human
Population (Q33829), Color (Q1075), Treatment
(Q179661), Symptom (Q169872), Anatomical
Structure (Q4936952), Sport (Q349), Animal
(Q729)."""


class GraspLinker(AbstractEntityLinker):
    """
    Connects to a grasp server to perform entity linking in texts for elevant benchmark.
    """
    def __init__(self, entity_db: EntityDatabase, config: dict[str, Any]) -> None:
        self.model = None
        self.entity_db = entity_db
        self.url = config["url"] # url of the grasp server
        self.log_directory = config.get("log_output_directory", "")
        self.benchmark = config.get("benchmark_name_for_logging", "benchmark")
        self.overlap = config.get("overlap_between_windows", 50)
        self.window_size = config.get("window_size", 400)
        self.num_retries = config.get("num_retries", 5)
        self.num_parallel = config.get("num_parallel", 3)
        self.num_allowed_timeouts = config.get("num_allowed_timeouts", 3)
        self.seconds_between_retries = config.get("seconds_between_retries", 10)
        self.resend_if_timeout = config.get("resend_if_timeout_in_output", True)
        self.log_path = os.path.join(self.log_directory, f"{self.benchmark}.jsonl")
        self.instructions = config.get("instructions", "")
        self.text_counter = 0
        try:
            os.remove(self.log_path)
        except:
            pass
        os.makedirs(self.log_directory, exist_ok=True)


    def get_text_split_indices(
            self,
            text: str,
            eval_span: tuple[int, int]| None = None
        ) -> list[tuple[int, int]]:
        result = []
        last_split = 0
        end = len(text)
        if eval_span:
            last_split, end = eval_span
        while last_split + self.window_size < end:
            next_last_split = last_split + self.window_size - self.overlap
            current_split = last_split + self.window_size
            result += [(last_split, current_split)]
            last_split = next_last_split

        result += [(last_split, end)]
        return result


    # required format for elevant
    def dict_to_preds(
            self,
            predictions: list[dict],
        ) -> dict[tuple[int, int], EntityPrediction]:
        result = {}
        for pred in predictions:
            s, e = pred["start"], pred["end"]
            ent = pred["entity"]
            if ent:
                ent = ent[3:] if ent[0:3] == "wd:" else ent
            else:
                ent = "<NIL>"
            result[(s, e)] = EntityPrediction((s, e), ent, {ent})
        return result


    # cut predictions that start beyond the overlap point where the next window starts
    # since those should be fully contained in the next excerpt
    def cut_overlap(
            self,
            predictions: list[dict],
            cut_beyond: int,
        ) -> list[dict]:
        result = [pred for pred in predictions if pred["start"] < cut_beyond]
        return result


    def send_a_request(self, text: dict) -> dict:
        rq = {"task": "entity-linking", "input": text, "knowledge_graphs": ["wikidata"]}
        rq = Request(
            self.url,
            data=json.dumps(rq).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"}
        )
        #for retry in range(self.num_retries + 1):
        retry = 0
        while retry < self.num_retries:
            try:
                with urlopen(rq) as response:
                    response = json.load(response)
            # general errors sending the request
            except Exception as e:
                print(
                    f"Error sending request for excerpt [{text['annotate_start']}: "
                    f"{text['annotate_end']}], "
                )
                time.sleep(self.seconds_between_retries)
                continue

            # look for words 'SPARQL query timed out' in the results
            predictions = response.get("output", {}).get("annotations", [])
            if self.resend_if_timeout and retry < self.num_retries:
                timeout_counter = 0
                messages = response.get("messages", [])
                for message in messages:
                    timeout_counter += str(message).count("SPARQL query timed out")
                if timeout_counter > self.num_allowed_timeouts:
                    print(
                        f"Too many timeouts ({timeout_counter}/{self.num_allowed_timeouts}), resending excerpt "
                        f"[{text['annotate_start']}: {text['annotate_end']}], "
                        f"{self.num_retries - retry} retries left."
                    )
                    retry += 1
                    continue

            # look for errors given by GRASP
            err = response.get("error", None)
            if err:
                print(
                    f"Error: {err} from GRASP. Resending excerpt "
                    f"[{text['annotate_start']}: {text['annotate_end']}]."
                )
                time.sleep(self.seconds_between_retries)
                continue

            # only log if successfull
            with open(self.log_path, "a") as logfile:
                json.dump(response, logfile)
                logfile.write("\n")

            print(f"Annotated excerpt [{text['annotate_start']}: {text['annotate_end']}]")
            return predictions
        return {}


    def predict(
            self,
            text: str,
            doc=None,
            uppercase: Optional[bool] = False,
            evaluation_span: tuple[int, int] | None = None
        ) -> dict[tuple[int, int], EntityPrediction]:
        self.text_counter += 1

        # show the headline for every article that is currently being linked
        headline = text[0:50].split("\n")[0]
        print(f"\nText {self.text_counter} of lenght {len(text)}: '{headline}'")

        # split the text into smaller pieces and tell grasp which excerpts to annotate
        splits = self.get_text_split_indices(text, evaluation_span)
        if self.instructions == "fair":
            instructions = fair_instructions
        elif self.instructions == "named":
            instructions = named_instructions
        else:
            instructions = None

        texts = [{
            "data": text,
            "annotate_start": i,
            "annotate_end": j,
            "special_instructions": instructions,
        } for i, j in splits]

        with ThreadPoolExecutor(max_workers=self.num_parallel) as t:
            result_list = list(t.map(self.send_a_request, texts))

        for i in range(len(result_list) - 1):
            result_list[i] = self.cut_overlap(
                result_list[i],
                texts[i]["annotate_end"] - self.overlap
            )

        # convert to elevant predictions
        result = {}
        for res in result_list:
            result.update(self.dict_to_preds(res))
        return result


    def has_entity(self, entity_id: str) -> bool:
        return True

