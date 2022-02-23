from typing import Dict, Tuple, Iterator

import logging
import abc

from src.models.entity_prediction import EntityPrediction

logger = logging.getLogger("main." + __name__.split(".")[-1])


class AbstractPredictionReader(abc.ABC):

    @abc.abstractmethod
    def predictions_iterator(self) -> Iterator[Dict[Tuple[int, int], EntityPrediction]]:
        """
        Yields predictions for each article.

        :return: iterator over dictionaries with predictions for each article
        """
        raise NotImplementedError()
