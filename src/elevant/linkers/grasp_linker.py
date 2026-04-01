import requests, os, json, time
from typing import Optional, Any
from concurrent.futures import ThreadPoolExecutor
from elevant.models.entity_database import EntityDatabase
from elevant.models.entity_prediction import EntityPrediction
from elevant.linkers.abstract_entity_linker import AbstractEntityLinker


class GraspLinker(AbstractEntityLinker):
    """
    Connects to a grasp server to perform entity linking in texts for elevant benchmark.
    """
    def __init__(self, entity_db: EntityDatabase, config: dict[str, Any]) -> None:
        self.model = None
        self.entity_db = entity_db
        self.url = config["url"] # url of the grasp server
        self.log_directory = config.get("output_directory", "")
        self.benchmark = config.get("benchmark", "benchmark")
        self.overlap = config.get("overlap_between_windows", 32)
        self.window_size = config.get("window_size", 500)
        self.num_retries = config.get("num_retries", 3)
        self.num_parallel = config.get("num_parallel", 1)
        self.seconds_between_retries = config.get("seconds_between_retries", 20)
        self.resend_if_timeout = config.get("resend_request_if_timeout_in_output", False)
        self.log_path = os.path.join(self.log_directory, f"{self.benchmark}.jsonl")
        self.text_counter = 0
        try:
            os.remove(self.log_path)
        except:
            pass
        os.makedirs(self.log_directory, exist_ok=True)
    

    def get_text_split_indices(self, text: str) -> list[tuple[int, int]]:
        # alternative stupid version: result = [(i, i + self.window_size + self.overlap) for i in range(0, len(text), self.window_size)]
        result = []
        last_split = 0
        split_sequences = {". ", ", ", ": ", "; ", "\n"}
        while last_split + self.window_size < len(text):
            for i in range(self.overlap):
                if text[last_split + self.window_size + i-1: i] in split_sequences:
                    result += [(last_split, i)]
                    last_split = i
            

        result += [(last_split, len(text))]
        return result

    
    def dict_to_preds(self, input: dict) -> dict[tuple[int, int], EntityPrediction]:
        result = {}
        for pred in input:
            s, e = pred["start_char"], pred["end_char"]
            ent = pred["entity_reference"]
            ent = ent[3:] if ent[0:3] == "wd:" else ent
            result[(s, e)] = EntityPrediction((s, e), ent, {ent})
        return result


    def send_a_request(self, text: dict) -> dict:
        rq = {"task": "entity-linking", "input": text, "knowledge_graphs": ["wikidata"]}
        for retry in range(self.num_retries):
            try:
                response = requests.post(self.url, json=rq).json()
            except:
                print(f"Error sending request for {text['start']} to {text['end']}, "
                      f"{self.num_retries - retry - 1} retries left. ")
                time.sleep(self.seconds_between_retries)
                continue

            with open(self.log_path, "a") as logfile:
                json.dump(response, logfile)

            # look for the word 'timeout' in the log
            predictions = response.get("output", {}).get("predictions", [])
            if (self.resend_if_timeout and 
                "timeout" in response.get("output", {}).get("messages", "")
            ):
                print(f"resending excerpt from {text['start']} to {text['end']}")
                continue

            print(f"Annotated excerpt from {text['start']} to {text['end']}")
            return self.dict_to_preds(predictions)
        return {}


    def predict(
            self,
            text: str,
            doc=None,
            uppercase: Optional[bool] = False
        ) -> dict[tuple[int, int], EntityPrediction]:
        self.text_counter += 1

        headline = text[0:48].split("\n")[0]
        print(f"\nText {self.text_counter} of lenght {len(text)}: '{headline}'.")

        # split the text into smaller pieces and tell grasp which excerpts to annotate
        splits = self.get_text_split_indices(text)
        texts = [{"data": text, "start": i, "end": j } for i, j in splits]

        with ThreadPoolExecutor(max_workers=self.num_parallel) as t:
            result_list = list(t.map(self.send_a_request, texts))
        
        result = {}
        for res in result_list:
            result.update(res)
        return result


    def has_entity(self, entity_id: str) -> bool:
        return True