import logging
from typing import Iterator, Tuple, Dict

from pynif import NIFCollection

from src.models.entity_database import EntityDatabase
from src.models.entity_prediction import EntityPrediction
from src.utils.knowledge_base_mapper import KnowledgeBaseMapper
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
                    entity_id = KnowledgeBaseMapper.get_wikidata_qid(entity_uri, self.entity_db, verbose=True)
                    span = phrase.beginIndex, phrase.endIndex
                    predictions[span] = EntityPrediction(span, entity_id, {entity_id})
                # Add article text and predictions to mappings
                yield predictions, text
