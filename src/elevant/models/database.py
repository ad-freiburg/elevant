import lmdb
import atexit
from typing import Optional, Union, List, Iterator, Tuple, Set


class Database:
    def __init__(self, db_file: str, value_type: Optional[type] = str, separator: Optional[str] = ","):
        self.env = lmdb.open(db_file, readonly=True, lock=False)
        self.value_type = value_type
        self.separator = separator

        # Register a cleanup function to close the environment when the program exits
        atexit.register(self.env.close)

    def __getitem__(self, key: str) -> Union[str, List[str], Set[str], int]:
        """
        If the database values are multi-values, i.e. the value is actually a list,
        return a list, otherwise a string.
        """
        with self.env.begin() as txn:
            val = txn.get(key.encode("utf8")).decode("utf8")
            if self.value_type is list:
                return val.split(self.separator)
            elif self.value_type is set:
                return set(val.split(self.separator))
            elif self.value_type is int:
                return int(val)
            else:
                return val

    def __contains__(self, key: str) -> bool:
        if key is None or key == "":
            return False
        with self.env.begin() as txn:
            try:
                return txn.get(key.encode("utf8")) is not None
            except lmdb.BadValsizeError:
                return False

    def __len__(self) -> int:
        with self.env.begin() as txn:
            return txn.stat()["entries"]

    def values(self) -> Iterator[str]:
        with self.env.begin() as txn:
            with txn.cursor() as cursor:
                for key, value in cursor:
                    yield self.__getitem__(key.decode("utf8"))

    def keys(self) -> Iterator[str]:
        with self.env.begin() as txn:
            with txn.cursor() as cursor:
                for key, value in cursor:
                    yield key.decode("utf8")

    def items(self) -> Iterator[Tuple[str, str]]:
        with self.env.begin() as txn:
            with txn.cursor() as cursor:
                for key, value in cursor:
                    yield key.decode("utf8"), self.__getitem__(key.decode("utf8"))
