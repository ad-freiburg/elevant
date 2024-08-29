import logging
from typing import Dict, Tuple, Optional, Any

import json
import requests

from elevant.models.entity_database import EntityDatabase
from elevant.models.entity_prediction import EntityPrediction
from elevant.linkers.abstract_entity_linker import AbstractEntityLinker
from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper

logger = logging.getLogger("main." + __name__.split(".")[-1])


class BabelfyLinker(AbstractEntityLinker):
    def __init__(self, entity_db: EntityDatabase, config: Dict[str, Any]):
        self.entity_db = entity_db
        self.model = None

        # Get config variables
        self.linker_identifier = config["linker_name"] if "linker_name" in config else "Babelfy"
        self.ner_identifier = self.linker_identifier
        if "api_key" not in config or config["api_key"] in ("", "replace with your own API key"):
            logger.error("You need an API key in order to run the Babelfy Linker.\nSee "
                         "http://babelfy.org/guide for instructions on how to get the API key. "
                         "(It's easy!)\nThen set your personal API key in configs/babelfy.config.json .")
            raise RuntimeError('No valid Babelfy access token provided.')
        else:
            self.api_key = config["api_key"]

        self.api_url = 'https://babelfy.io/v1/disambiguate'

    def predict(self,
                text: str,
                doc=None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
        params = {
            'text': text,
            'lang': 'EN',
            'key': self.api_key
        }
        r = requests.post(self.api_url, data=params, headers={'Accept-encoding': 'gzip'})
        predictions = {}
        data = json.loads(str(r.content, 'utf-8'))
        try:
            for result in data:
                dbpedia_url = result.get('DBpediaURL')

                char_fragment = result.get('charFragment')
                start = char_fragment.get('start')
                end = char_fragment.get('end') + 1

                entity_id = KnowledgeBaseMapper.get_wikidata_qid(dbpedia_url, self.entity_db)
                span = (start, end)
                snippet = text[span[0]:span[1]]
                if uppercase and snippet.islower():
                    continue
                predictions[span] = EntityPrediction(span, entity_id, {entity_id})
        except AttributeError as e:
            # Print message from server and raise exception
            print()
            logger.error(data['message'])
            raise e

        return predictions

    def has_entity(self, entity_id: str) -> bool:
        return True
