# -*- coding: utf-8 -*-
import os
# import sys
import logging
logger = logging.getLogger(__name__)

MODULE_DIR = os.path.dirname(__file__)
REPO_DIR = os.path.dirname(MODULE_DIR)


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
