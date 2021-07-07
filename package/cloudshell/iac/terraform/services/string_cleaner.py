import re

from cloudshell.iac.terraform.constants import DIRTY_CHARS


class StringCleaner(object):

    @staticmethod
    def get_clean_string(dirty_str: str) -> str:
        ansi_escape = re.compile(DIRTY_CHARS, re.VERBOSE)
        clean_str = ansi_escape.sub('', dirty_str).encode('cp1252', errors='replace').decode('cp1252').replace("?", "")
        return clean_str
