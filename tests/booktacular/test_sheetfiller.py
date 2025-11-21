import json
import os
import pytest
import sys

from booktacular import (
    query_dict,
    key_of_value,
    REPO_DIR,
)
from booktacular.btpb2 import mappings
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


@pytest.fixture
def filled_svg_file(request, load_data):
    """Fixture to handle creation and cleanup of the filled SVG file."""
    source, meta, template_path = load_data

    # Choose the metadata matching the sheet:
    meta = meta['fillable-fields']

    # Initialize and populate the sheet
    sheet = BooktacularSheet()
    sheet.load(template_path)
    sheet.setMeta(meta)
    sheet.setMappings(mappings)
    # File path must be provided before setFields,
    #   otherwise first call setMappingsPath
    mappings_csv_dir = None
    new_dir = os.path.dirname(template_path)
    if mappings_csv_dir is None:
        mappings_csv_dir = new_dir
    mappings_csv_path = os.path.join(
        mappings_csv_dir,
        "booktacular-source-fields.csv",
    )
    sheet.setMappingsPath(mappings_csv_path)
    sheet.setFields(source)

    # for src, dst in mappings.items():
    #     value = query_dict(meta, src)
    #     sheet.setValueById(dst, value)

    no_ext, _ = os.path.splitext(template_path)
    filled_path = "{}.FILLED.svg".format(no_ext)

    # Save the filled SVG
    sheet.save(filled_path, overwrite=True)
    if os.path.isfile(filled_path):
        print("Saved \"{}\"".format(filled_path),
              file=sys.stderr)
    else:
        assert os.path.isfile(filled_path)

    # Register finalizer to remove the file
    def cleanup():
        if os.path.isfile(filled_path):
            pass
            print("Removing \"{}\"".format(filled_path),
                  file=sys.stderr)
            # os.remove(filled_path)

    request.addfinalizer(cleanup)

    return filled_path

# TODO: test filling (See
#   https://github.com/Hierosoft/e1p-character-sheet-for-pf2)

# def test_filled_svg_creation(filled_svg_file, load_data):
#     source, meta, template_path = load_data
#     filled_path = filled_svg_file

#     # Perform assertions on the filled SVG file
#     assert os.path.isfile(filled_path), "Filled SVG file not found: {}".format(filled_path)

#     filled = BooktacularSheet()
#     filled.load(filled_path)
#     # TODO: load included mappings by default? See
#     #   https://github.com/Hierosoft/e1p-character-sheet-for-pf2
#     #   for full example (manually loads the mappings)

#     nur_wonderfield = os.path.join(REPO_DIR,
#         "tests", "booktacular", "data",
#         "Nur_Wonderfield-pb2e.json")
#     mappings_dir = os.path.dirname(nur_wonderfield)
#     mappings_path = os.path.join(mappings_dir, "booktacular-source-fields.csv")
#     sheet = BooktacularSheet()
#     sheet.load(template_path)
#     assert "armor_class_" in mappings.values()
#     xpath = key_of_value(mappings, "armor_class_")
#     good_p = "/build/acTotal/acTotal"
#     assert xpath == good_p, "key_of_value({}) {} != {}".format("armor_class_", xpath, good_p)
#     src_v = query_dict(source, xpath)
#     nur_ac = 17
#     # Has to be converted to str during setFields
#     #   to prevent TypeError in serialization in xml
#     #   in Python 3.8.19 (and is loaded as str
#     #   like everything) so cast to int below.
#     # First check the source data file:
#     assert int(src_v) == nur_ac, "{} != {}".format(src_v, nur_ac)
#     # Now check the rewritten svg file:
#     out_ac = filled.getContent("armor_class_")
#     assert int(out_ac) == int(src_v), "{} != {}".format(out_ac, src_v)
