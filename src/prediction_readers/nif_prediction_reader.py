import logging
import re
from typing import Iterator, Tuple, Dict

from pynif import NIFCollection
from urllib.parse import unquote

from src.models.entity_database import EntityDatabase
from src.models.entity_prediction import EntityPrediction
from src.prediction_readers.abstract_prediction_reader import AbstractPredictionReader

logger = logging.getLogger("main." + __name__.split(".")[-1])


class NifPredictionReader(AbstractPredictionReader):
    def __init__(self, input_filepath: str, entity_db: EntityDatabase):
        self.entity_db = entity_db
        super().__init__(input_filepath, predictions_iterator_implemented=False)

    def get_predictions_with_text_from_file(self, filepath: str) -> Iterator[Tuple[Dict[Tuple[int, int],
                                                                                        EntityPrediction], str]]:
        """
        Yields predictions and article text for each article in the file

        :return: iterator over dictionaries with predictions for each article and the article text
        """
        with open(filepath, "r", encoding="utf8") as file:
            file_content = file.readlines()
            nif_content = "".join(file_content)
            nif_doc = NIFCollection.loads(nif_content)
            for context in nif_doc.contexts:
                text = context.mention
                if not text:
                    # This happens e.g. in KORE50 for the parent context
                    # <http://www.mpi-inf.mpg.de/yago-naga/aida/download/KORE50.tar.gz/AIDA.tsv>
                    continue
                predictions = {}
                for phrase in context.phrases:
                    entity_uri = phrase.taIdentRef
                    entity_name = entity_uri[entity_uri.rfind("/") + 1:]
                    # The entity ID will be None if the provided entity ID
                    # is not a QID or cannot be mapped from Wikipedia title to QID
                    if entity_name and not re.match(r"Q[0-9]+", entity_name):
                        entity_name = unquote(entity_name).replace('_', ' ')
                        entity_id = self.entity_db.link2id(entity_name)
                        if not entity_id:
                            logger.warning("Entity name %s could not be mapped to a Wikidata ID." % entity_name)
                    else:
                        entity_id = entity_name
                    span = phrase.beginIndex, phrase.endIndex
                    predictions[span] = EntityPrediction(span, entity_id, {entity_id})

                # Add article text and predictions to mappings
                yield predictions, text
