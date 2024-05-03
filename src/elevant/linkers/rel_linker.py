import logging
from typing import Dict, Tuple, Optional, Any

import os
import tarfile
import requests
import urllib.request

from elevant import settings
from elevant.models.entity_database import EntityDatabase
from elevant.models.entity_prediction import EntityPrediction
from elevant.linkers.abstract_entity_linker import AbstractEntityLinker
from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper

from REL.mention_detection import MentionDetection
from REL.utils import process_results
from REL.entity_disambiguation import EntityDisambiguation
from REL.ner import Cmns, load_flair_ner


logger = logging.getLogger("main." + __name__.split(".")[-1])


def download_and_extract(url: str, base_path: str):
    """
    Download and extract the given url at the given path if it does not exist
    already.
    """
    # Prepare the file and path names
    tar_filename = url[url.rfind("/") + 1:]
    tar_path = base_path + tar_filename
    path = base_path + tar_filename[0:tar_filename.find(".")]

    if not os.path.exists(path):
        logger.info("Downloading and extracting %s" % url)
        # Download the file
        urllib.request.urlretrieve(url, tar_path)

        # Extract the file
        file = tarfile.open(tar_path)
        file.extractall(base_path)
        file.close()
        logger.info("Saved file at %s" % path)


class RelLinker(AbstractEntityLinker):
    def __init__(self, entity_db: EntityDatabase, config: Dict[str, Any]):
        self.entity_db = entity_db
        self.model = None

        # Get config variables
        self.linker_identifier = config["linker_name"] if "linker_name" in config else "REL"
        self.ner_identifier = self.linker_identifier

        self.use_api = config["use_api"] if "use_api" in config else False
        self.api_url = config["api_url"] if "api_url" in config else "https://rel.cs.ru.nl/api"

        if not self.use_api:
            base_url = config["base_url"] if "base_url" in config else settings.LINKER_FILES + "rel/"
            base_url = base_url.rstrip("/") + "/"
            wiki_version = config["wiki_version"] if "wiki_version" in config else "wiki_2019"
            ner_model = config["ner_model"] if "ner_model" in config else "ner-fast"

            # Download the data if it does not exist yet
            if not os.path.exists(base_url):
                logger.info("Creating directory %s" % base_url)
                os.makedirs(base_url)
            download_and_extract("http://gem.cs.ru.nl/generic.tar.gz", base_url)
            if wiki_version == "wiki_2014":
                download_and_extract("http://gem.cs.ru.nl/wiki_2014.tar.gz", base_url)
                download_and_extract("http://gem.cs.ru.nl/ed-wiki-2014.tar.gz", base_url)
            elif wiki_version == "wiki_2019":
                download_and_extract("http://gem.cs.ru.nl/wiki_2019.tar.gz", base_url)
                download_and_extract("http://gem.cs.ru.nl/ed-wiki-2019.tar.gz", base_url)

            self.md_model = MentionDetection(base_url, wiki_version)
            if ner_model == "ngram":
                self.ner_tagger = Cmns(base_url, wiki_version, n=5)
            else:
                self.ner_tagger = load_flair_ner(ner_model)
            ed_config = {"mode": "eval", "model_path": f"{base_url}/{wiki_version}/generated/model"}
            self.ed_model = EntityDisambiguation(base_url, wiki_version, ed_config)

    def predict(self,
                text: str,
                doc=None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
        if self.use_api:
            # Query the API at the specified URL for predictions
            annotations = requests.post(self.api_url, json={"text": text, "spans": []}).json()
        else:
            # Use the locally installed REL module and the downloaded data
            input_text = {"doc": [text, []]}
            mentions_dataset, n_mentions = self.md_model.find_mentions(input_text, self.ner_tagger)
            predictions, timing = self.ed_model.predict(mentions_dataset)
            annotations = process_results(mentions_dataset, predictions, input_text)
            annotations = annotations["doc"] if "doc" in annotations else {}

        predictions = {}
        for ann in annotations:
            entity_name = ann[3]
            entity_id = KnowledgeBaseMapper.get_wikidata_qid(entity_name, self.entity_db)
            span = (ann[0], ann[0] + ann[1])
            snippet = text[span[0]:span[1]]
            if uppercase and snippet.islower():
                continue
            predictions[span] = EntityPrediction(span, entity_id, {entity_id})
        return predictions

    def has_entity(self, entity_id: str) -> bool:
        return True
