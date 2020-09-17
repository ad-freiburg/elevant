from dateutil.parser import parse


def is_date(text: str) -> bool:
    try:
        parse(text, ignoretz=True)
        return True
    except:
        return False
