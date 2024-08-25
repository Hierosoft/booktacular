import pytest
from typing import Union, Generator

from booktacular import pairs

# Assuming the function to be tested is named `pairs`
# from your_module import pairs

def test_pairs_with_list():
    input_data = ['foo', 'spam']
    expected_output = [(0, 'foo'), (1, 'spam')]
    result = list(pairs(input_data))
    assert result == expected_output

def test_pairs_with_dict():
    input_data = {'foo': 'value1', 'spam': 'eggs'}
    expected_output = [('foo', 'value1'), ('spam', 'eggs')]
    result = list(pairs(input_data))
    assert result == expected_output

def test_pairs_with_invalid_type():
    input_data = "apple"
    with pytest.raises(TypeError):
        list(pairs(input_data))

