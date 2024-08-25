# -*- coding: utf-8 -*-
from __future__ import annotations  # Union[ and possibly others
from typing import Union, Generator

import os
# import sys
import logging

logger = logging.getLogger(__name__)

MODULE_DIR = os.path.dirname(__file__)
REPO_DIR = os.path.dirname(MODULE_DIR)


class PairsTypeError(TypeError):
    pass


def emit_cast(value):
    # formerly typed_name
    return "{}({})".format(type(value).__name__, repr(value))


def pairs(data: Union[list, dict]) -> Generator:
    """Generate key-value pairs from a list or dictionary.

    Args:
        data (Union[list, dict]): The input data, which must be a list or dictionary.

    Yields:
        tuple: A tuple containing the key (or index) and the corresponding value.

    Raises:
        TypeError: If the input data is not a list or dictionary.
    """
    if isinstance(data, list):
        yield from enumerate(data)
    elif isinstance(data, dict):
        yield from data.items()
    else:
        raise PairsTypeError(
            "Only dict or list is allowed, but got {}"
            .format(emit_cast(data)))
    # ok to get here after yield finishes, apparently
    # logger.warning(
    #     "[pairs] dumping after no yield {}".format(emit_cast(data)))


def endswith_any(haystack, needles):
    for needle in needles:
        if haystack.endswith(needle):
            return True
    return False


def find_which(haystack, needles):
    """Find needle's location closest to the beginning & its own index

    Args:
        haystack (str): Any string to search.
        needles (tuple[str]): Criteria to find in haystack.

    Returns:
        tuple(int): location of needle closest to start of haystack else
            -1, then index of needle if haystack index is not -1
    """
    result = -1
    needle_result = -1
    for needle_i, needle in enumerate(needles):
        i = haystack.find(needle)
        if (result == -1) or (i > -1 and i < result):
            result = i
            needle_result = needle_i
    return result, needle_result


def find_any(haystack, needles):
    """Find the instance of the needle that is closest to the beginning

    Args:
        haystack (str): Any string to search.
        needles (tuple[str]): Criteria to find in haystack.

    Returns:
        int: location of needle closest to start of haystack, or -1.
    """
    result = -1
    for needle in needles:
        i = haystack.find(needle)
        if (result == -1) or (i > -1 and i < result):
            result = i
    return result


def querydict(d, q):
    # based on <https://stackoverflow.com/a/7320730/4541104>
    # MarcoS. Sep 6, 2011. Accessed Aug 23, 2024.
    if not isinstance(q, str):
        raise TypeError("query path must be str but got {}"
                        .format(emit_cast(q)))
    keys = q.split('/')
    nd = d
    for  k  in  keys:
        if  k == '':
            continue
        if  k  in  nd:
            nd = nd[k]
        else:
            return  None
    return  nd


def get_all_queries(d, parent=""):
    queries = []
    if isinstance(d, (list, dict)):
        for k, v in pairs(d):
            if isinstance(v, (list, dict)):
                if not v:
                    # empty list or dict, so recursion would show
                    #   nothing. therefore treat this as a leaf, so user
                    #   can get set or get [] or {}.
                    queries.append("{}/{}".format(parent, k))
                else:
                    queries += get_all_queries(v, "{}/{}".format(parent, k))
            else:
                queries.append("{}/{}".format(parent, k))
    else:
        raise RecursionError(
            "Cannot determine path since got value without key(s): {}"
            .format(d))
    return queries


def key_of_value(d, value):
    keys = {k for k in d if d[k]==value}  # gets a set()
    key = keys.pop()
    if keys:
        raise ValueError(
            "More than one key ({}) has value {}"
            .format(repr(set(key).union(keys)),
                    repr(value))
        )
    return key
