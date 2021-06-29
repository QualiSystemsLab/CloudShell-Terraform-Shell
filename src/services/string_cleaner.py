import re

from constants import DIRTY_CHARS


class StringCleaner(object):

    @staticmethod
    def get_clean_string(dirty_str: str) -> str:
        ansi_escape = re.compile(DIRTY_CHARS, re.VERBOSE)
        return ansi_escape.sub('', dirty_str)
