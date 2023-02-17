import dbm
from typing import Optional, Union, List, Iterator, Tuple, Set


class Database:
    def __init__(self, db: dbm, value_type: Optional[type] = str, separator: Optional[str] = ","):
        self.db = db
        self.value_type = value_type
        self.separator = separator

    def __getitem__(self, key: str) -> Union[str, List[str], Set[str], int]:
        """
        If the database values are multi-values, i.e. the value is actually a list,
        return a list, otherwise a string.
        """
        val = self.db[key].decode("utf8")
        if self.value_type is list:
            return val.split(self.separator)
        elif self.value_type is set:
            return set(val.split(self.separator))
        elif self.value_type is int:
            return int(val)
        else:
            return val

    def __contains__(self, key: str) -> bool:
        if key is None:
            return False
        return key in self.db

    def __len__(self) -> int:
        return len(self.db)

    def values(self) -> Iterator[str]:
        k = self.db.firstkey()
        while k is not None:
            yield self.__getitem__(k)
            k = self.db.nextkey(k)

    def keys(self) -> Iterator[str]:
        k = self.db.firstkey()
        while k is not None:
            yield k.decode("utf8")
            k = self.db.nextkey(k)

    def items(self) -> Iterator[Tuple[str, str]]:
        k = self.db.firstkey()
        while k is not None:
            yield k.decode("utf8"), self.__getitem__(k)
            k = self.db.nextkey(k)
