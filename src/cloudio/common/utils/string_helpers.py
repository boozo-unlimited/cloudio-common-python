# -*- coding: utf-8 -*-

import re


def camel_case_split(string: str, lower_camel_case: bool = False) -> list:
    """Splits a camel-case formatted string into its wors.

    Example: 'ANiceDay' gets converted to ['A', 'Nice', 'Day'].

    If lower_camel_case is specified, also the first expression is put into the list.

    Credits to:
    - https://www.geeksforgeeks.org/python-split-camelcase-string-to-individual-strings/
    - https://stackoverflow.com/questions/29916065/how-to-do-camelcase-split-in-python
    """

    if not lower_camel_case:
        return re.findall(r'[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', string)
    else:
        idx = list(map(str.isupper, string))
        # mark change of case
        lst = [0]
        for (i, (x, y)) in enumerate(zip(idx, idx[1:])):
            if x and not y:  # "Ul"
                lst.append(i)
            elif not x and y:  # "lU"
                lst.append(i + 1)
        lst.append(len(string))
        # for "lUl", index of "U" will pop twice, have to filter it
        return [string[x:y] for x, y in zip(lst, lst[1:]) if x < y]
