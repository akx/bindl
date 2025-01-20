from __future__ import annotations

import os
import re
import string


def make_any_match(regexps: list[re.Pattern]):
    return lambda value: any(pat.match(value) for pat in regexps)


FILTERS = {
    "basename": lambda x: os.path.basename(x),
    "strip_ext": lambda x: os.path.basename(x).partition(".")[0],
}


class FilteringFormatter(string.Formatter):
    def get_value(self, key, args, kwargs):
        key, *filters = (bit.strip() for bit in key.split("|"))
        value = super().get_value(key, args, kwargs)
        for filter in filters:
            value = FILTERS[filter](value)
        return value
