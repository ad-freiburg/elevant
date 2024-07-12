import os
import logging

from typing import Dict, Tuple, Iterator
from xml.etree import ElementTree

from elevant.models.entity_database import EntityDatabase
from elevant.models.entity_prediction import EntityPrediction
from elevant.prediction_readers.abstract_prediction_reader import AbstractPredictionReader
from elevant.utils.knowledge_base_mapper import KnowledgeBaseName, KnowledgeBaseMapper

logger = logging.getLogger("main." + __name__.split(".")[-1])


class WikifierPredictionReader(AbstractPredictionReader):
    def __init__(self, input_filepath: str, entity_db: EntityDatabase):
        self.entity_db = entity_db
        super().__init__(input_filepath, predictions_iterator_implemented=True)

    @staticmethod
    def is_same_title(unicode_error_title: str, title: str) -> bool:
        if title is None:
            return False
        error_indices = [i for i, char in enumerate(unicode_error_title) if char == "?"]
        new_title = ''.join([char for i, char in enumerate(title) if i not in error_indices])
        return new_title == unicode_error_title.replace("?", "")

    def get_correct_wikipedia_title(self, wiki_title: str, wiki_id: int) -> str:
        """
        For the Wikipedia title and Wikipedia page ID predicted by Wikifier
        retrieve the corresponding Wikidata ID.
        """
        wiki_title_by_id = self.entity_db.get_wikipedia_title_by_wikipedia_id(wiki_id)
        # The Wikifier output labels contain encoding errors indicated by the character "?".
        # Use the Wikipedia page ID to try to map the linked entity to a Wikidata QID anyway.
        if wiki_title != wiki_title_by_id and "?" in wiki_title:
            if wiki_id != 3658264 and wiki_title_by_id is not None:
                # There is an error in the Wikifier output: many page ids in the Wikifier result
                # are 3658264 which corresponds to the Wikipedia title "Williams Lake Water Aerodrome"
                # Others point to an empty page. Keep the WikiTitle in this case, otherwise use
                # the title extracted via the page ID
                wiki_title = wiki_title_by_id
            else:
                logger.warning("Could not resolve missing characters in '%s', title by page ID: '%s', ID: %d"
                               % (wiki_title, wiki_title_by_id, wiki_id))
        return wiki_title

    def _get_prediction_from_file(self, file_path: str) -> Dict[Tuple[int, int], EntityPrediction]:
        """
        Yields all predictions in the given wikifier disambiguation result file

        :param file_path: path to the wikifier result file
        :return: dictionary that contains all predictions for the given file
        """
        predictions = {}
        xml_tree = ElementTree.parse(file_path)
        root = xml_tree.getroot()
        count = 0
        for entity_prediction in root.iter('Entity'):
            start = int(entity_prediction.find('EntityTextStart').text)
            end = int(entity_prediction.find('EntityTextEnd').text)
            span = start, end

            wiki_title = entity_prediction.find('TopDisambiguation').find('WikiTitle').text
            wiki_title = wiki_title.replace("_", " ")
            wiki_id = int(entity_prediction.find('TopDisambiguation').find('WikiTitleID').text)
            # Wikifier predicted entity IDs can contain mistakes, therefore use custom rules to map entites to
            # Wikidata QIDs instead of using KnowledgeBaseMappingl.get_wikidata_qid()
            wiki_title = self.get_correct_wikipedia_title(wiki_title, wiki_id)
            entity_id = KnowledgeBaseMapper.get_wikidata_qid(wiki_title, self.entity_db,
                                                             kb_name=KnowledgeBaseName.WIKIPEDIA)
            if KnowledgeBaseMapper.is_unknown_entity(entity_id):
                logger.warning("No mapping to Wikidata found for label '%s'" % wiki_title)
                count += 1

            candidates = set()
            for candidate in entity_prediction.find('DisambiguationCandidates').iter('Candidate'):
                candidate_wiki_title = candidate.find('WikiTitle').text
                candidate_wiki_title = candidate_wiki_title.replace("_", " ")
                candidate_wiki_id = int(entity_prediction.find('TopDisambiguation').find('WikiTitleID').text)
                candidate_wiki_title = self.get_correct_wikipedia_title(candidate_wiki_title, candidate_wiki_id)
                candidate_entity_id = KnowledgeBaseMapper.get_wikidata_qid(candidate_wiki_title, self.entity_db,
                                                                           kb_name=KnowledgeBaseName.WIKIPEDIA)
                if not KnowledgeBaseMapper.is_unknown_entity(candidate_entity_id):
                    candidates.add(candidate_entity_id)

            # Note that Wikifier produces overlapping spans
            predictions[span] = EntityPrediction(span, entity_id, candidates)

        if count > 0:
            logger.warning("%d entity labels could not be matched to any Wikidata ID." % count)

        return predictions

    def predictions_iterator(self) -> Iterator[Dict[Tuple[int, int], EntityPrediction]]:
        """
        Yields predictions for each wikfier disambiguation result file in the disambiguation_dir.

        :return: iterator over dictionaries with predictions for each article
        """
        for file in sorted(os.listdir(self.input_filepath)):
            if file.endswith(".full.xml"):
                file_path = os.path.join(self.input_filepath, file)
                predictions = self._get_prediction_from_file(file_path)
                yield predictions
