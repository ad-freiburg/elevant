import logging
from typing import Iterator, Tuple, Dict, Optional

from pynif import NIFCollection

from elevant.models.entity_database import EntityDatabase
from elevant.models.entity_prediction import EntityPrediction
from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper, UnknownEntity
from elevant.prediction_readers.abstract_prediction_reader import AbstractPredictionReader

logger = logging.getLogger("main." + __name__.split(".")[-1])


class NifPredictionReader(AbstractPredictionReader):
    def __init__(self, input_filepath: str, entity_db: EntityDatabase, custom_kb: Optional[bool] = False):
        self.entity_db = entity_db
        self.custom_kb = custom_kb
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
            # NIF contexts have random order by default. Make sure results are reproducible by sorting by URI
            for context in sorted(nif_doc.contexts, key=lambda c: c.uri):
                text = context.mention
                if not text:
                    # This happens e.g. in KORE50 for the parent context
                    # <http://www.mpi-inf.mpg.de/yago-naga/aida/download/KORE50.tar.gz/AIDA.tsv>
                    continue
                predictions = {}
                # Make sure predictions are sorted by start index
                for phrase in sorted(context.phrases, key=lambda p: p.beginIndex):
                    entity_uri = phrase.taIdentRef
                    if self.custom_kb:
                        entity_id = entity_uri if entity_uri else UnknownEntity.NIL.value
                    else:
                        entity_id = KnowledgeBaseMapper.get_wikidata_qid(entity_uri, self.entity_db, verbose=True)
                    span = phrase.beginIndex, phrase.endIndex
                    predictions[span] = EntityPrediction(span, entity_id, {entity_id})
                # Add article text and predictions to mappings
                yield predictions, text
