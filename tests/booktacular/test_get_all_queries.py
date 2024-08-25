import json
import pytest

from collections import OrderedDict

from booktacular import get_all_queries


def test_get_all_queries_simple_dict():
    # input_data = {
    #     "build": {
    #         "acTotal": {
    #             "acProfBonus": 3,
    #             "acItemBonus": 2
    #         }
    #     }
    # }
    input_data = OrderedDict()
    input_data["build"] = OrderedDict()
    input_data["build"]["acTotal"] = OrderedDict()
    input_data["build"]["acTotal"]["acProfBonus"] = 3
    input_data["build"]["acTotal"]["acItemBonus"] = 2
    expected_output = [
        "/build/acTotal/acProfBonus",
        "/build/acTotal/acItemBonus"
    ]
    queries = get_all_queries(input_data)
    assert queries == expected_output

def test_get_all_queries_nested_dict():
    input_data = {
        "build": {
            "acTotal": {
                "acTotal": {
                    "acProfBonus": 3,
                    "acItemBonus": 2
                }
            }
        }
    }
    expected_output = [
        "/build/acTotal/acTotal/acProfBonus",
        "/build/acTotal/acTotal/acItemBonus"
    ]
    assert get_all_queries(input_data) == expected_output

def test_get_all_queries_with_list():
    # input_data = {
    #     "formula": [],
    #     "build": {
    #         "acTotal": {
    #             "acProfBonus": 3,
    #             "acItemBonus": 2
    #         }
    #     }
    # }
    input_data = OrderedDict()
    input_data["formula"] = []
    input_data["build"] = OrderedDict()
    input_data["build"]["acTotal"] = OrderedDict()
    input_data["build"]["acTotal"]["acProfBonus"] = 3
    input_data["build"]["acTotal"]["acItemBonus"] = 2

    expected_output = [
        "/formula",
        "/build/acTotal/acProfBonus",
        "/build/acTotal/acItemBonus"
    ]
    queries = get_all_queries(input_data)
    # raise ValueError("queries={}".format(json.dumps(queries)))
    assert queries == expected_output
