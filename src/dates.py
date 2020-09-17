import re

from dateutil.parser import parse


_DATE_RE = re.compile("([0-9]{1,2} )?(January|February|March|April|May|June|July|August|September|October|November|December)( [0-9]{1,4})?")


def is_date_by_re(text: str) -> bool:
    return bool(_DATE_RE.fullmatch(text))


def is_date(text: str) -> bool:
    try:
        parse(text, ignoretz=True)
        return True
    except:
        return False
