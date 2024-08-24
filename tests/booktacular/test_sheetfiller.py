import json
import os
import pytest
from booktacular import querydict
from booktacular.morepb2 import mappings
from booktacular.sheetfiller import BooktacularSheet

@pytest.fixture
def setup_paths():
    """Fixture to set up file paths."""
    test_dir = os.path.dirname(os.path.realpath(__file__))
    data_dir = os.path.join(test_dir, "data")
    meta_path = os.path.join(data_dir, "sheet-fields.json")
    data_path = os.path.join(data_dir, "Nur_Wonderfield-pb2e.json")
    template_path = os.path.join(data_dir, "demo_sheet.svg")

    # Ensure the required files exist
    for path in (meta_path, data_path, template_path):
        if not os.path.isfile(path):
            pytest.fail(f"Required file not found: {path}")

    yield meta_path, data_path, template_path

@pytest.fixture
def load_data(setup_paths):
    """Fixture to load data and meta from JSON files."""
    meta_path, data_path, template_path = setup_paths

    with open(data_path, 'r') as stream:
        source = json.load(stream)
    with open(meta_path, 'r') as stream:
        meta = json.load(stream)

    return source, meta, template_path

def test_filled_svg_creation(load_data):
    source, meta, template_path = load_data

    # Initialize and populate the sheet
    sheet = BooktacularSheet()
    sheet.load(template_path)

    for src, dst in mappings.items():
        value = querydict(src, meta)
        sheet.setValueById(dst, value)

    no_ext, _ = os.path.splitext(template_path)
    filled_path = "{}.FILLED.svg".format(no_ext)

    # Save the filled SVG
    sheet.save(filled_path)

    # Assert that the filled SVG file exists
    assert os.path.isfile(filled_path), f"Filled SVG file not found: {filled_path}"

    # TODO: load the file and compare against desired values.

    # Optionally, clean up the created file
    if os.path.isfile(filled_path):
        os.remove(filled_path)
