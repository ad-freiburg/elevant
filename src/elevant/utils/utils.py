def convert_to_filename(string: str):
    """
    Return lowercased version of the given string with non-alphanumerical
    characters replaced by underscore (except for "-").
    """
    return "".join(c if c.isalnum() or c == "-" else "_" for c in string.lower())