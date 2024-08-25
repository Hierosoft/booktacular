import json
import os
import sys

from logging import getLogger

from pyinkscape import (
    Canvas,
)

from pyinkscape.inkscape import (
    used_elements,
)

if __name__ == "__main__":
    MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.dirname(MODULE_DIR))

from booktacular import (
    get_all_queries,
    querydict,
)

logger = getLogger(__name__)

# TODO: from pyinkscape.render import svg_to_pdf

FIELD_META_KEYS = [
    "tip", "value_line_style_template", "choices",
    "deletes", "append_variable", "prefix", "suffix",
    "base_attribute_", "rules", "default",
    "recommended_max_characters", "max_characters",
    "lines", "lambda", "value_deletes", "value_properties",
    "delete_if_not", "keep", "line_prefix", "tally_indent"],
# TODO: implement globals (such as those used by delete_if_not, and others starting with _)
# TODO: if keep, keep initial value in sheet unless set (or deleted by a condition)
# TODO: if tally_indent is set, code can indent that much if ability has a tally (is not cantrip)
RULES_META_KEYS = ["lambdas"]
LAMBDA_OPERATORS = ["+"]
LAMBDA_FUNCTIONS = ["min", "if"]

DEFAULTS = {
    "heightened_help_": """<tspan
         x="508.15039"
         y="683.70031"
         id="tspan54766"><tspan
           style="font-family:'Fira Sans Condensed';-inkscape-font-specification:'Fira Sans Condensed, ';fill:#808080"
           id="tspan54760">Cantrips &amp; Focus spells </tspan><tspan
           style="font-weight:bold;font-family:'Fira Sans';-inkscape-font-specification:'Fira Sans'"
           id="tspan54762">heightened</tspan><tspan
           style="font-family:'Fira Sans Condensed';-inkscape-font-specification:'Fira Sans Condensed, ';fill:#808080"
           id="tspan54764"> by caster level/2: round up.
</tspan></tspan>"""
}


class BooktacularSheet:
    def __init__(self):
        self._doc = None
        self._path = None
        self._meta = None
        self._mappings = None

    def load(self, path):
        self._doc = Canvas(path)
        self._path = path

    def set_meta(self, meta):
        """Set the SVG's usage metadata for fields by name"""
        self._meta = meta

    def set_mappings(self, mappings):
        """Set dict that maps data json paths to SVG field names"""
        self._mappings = mappings

    def set_values(self, source):
        """Set all of the values possible in SVG from source

        Args:
            source (dict): Character data, such as representing a JSON
                file exported by PB2e
        """
        results = {
            "missing_source_fields": [],
            "missing_template_fields": [],
        }
        no_dst_key = set()
        no_src_key = set()
        dst_keys = set()
        src_keys = set()
        used_src_keys = get_all_queries(source)
        used_dst_keys = set()
        if no_dst_key:
            logger.warning("Source fields with no destination field: {}"
                           .format(no_dst_key))
        if no_src_key:
            logger.warning("Destination fields with no source field: {}"
                           .format(no_src_key))
        for xpath, field in self._mappings.items():
            new = querydict(source, xpath)
            if new is None:
                results['missing_source_fields'].append(xpath)
                msg = "data source is missing {}".format(xpath)
                logger.warning(msg)
                continue
            leaves = self._doc.getLeavesById(
                field, "text", "tspan", only_placeholders=False)
            # ^ FIXME: For some reason not all placeholders are
            #   detected, so only_placeholders=False is
            #   necessary. Therefore, set value on
            #   first non-empty one below.
            if not leaves:
                results['missing_template_fields'].append(xpath)
                msg = ("sheet is missing text or group"
                       " with id={} containing a tspan"
                       .format(repr(xpath)))
                logger.warning(msg)
            count = 0
            for leaf in leaves:
                if leaf.text:
                    leaf.text = str(new)
                    new = ""  # clear all others
                else:
                    leaf.text = ""
                # ^ FIXME: report xml issue to Python team??:
                #   - if int, works now but raises TypeError on save
                #     when trying to do `if "&" in text:` in _escape_cdata
                #     method in xml/etree/ElementTree.py 3.8.19
                # ^ prevents odd transformations of same text caused by
                #   Inkscape generating multiple text tags for same
                #   text.
                count += 1
            if count > 1:
                logger.warning("blanked {} extra copies of {}"
                               .format(count-1, field))
            else:
                logger.warning("blanked no extra copies of {}"
                               .format(field))
        return results

    def getContent(self, ID):
        # formerly getValueById
        leaves = self._doc.getLeavesById(
            ID, "text", "tspan", only_placeholders=True)
        if not leaves:
            return None
        if len(leaves) > 1:
            used = used_elements(leaves)
            return used[0]
        return leaves[0].text

    def getElementById(self, ID):
        # get all existing layers
        # layers = self._doc.layers()
        # # get a layer by name
        # layer1 = self._doc.layer("Layer 1")
        # # get a layer by ID
        # layer1 = self._doc.layer_by_id("layer1")
        elements = self._doc.getLeavesById(
            ID, "text", "tspan", only_placeholders=True)
        if len(elements) < 1:
            raise ValueError("{} is missing id {}".format(self._path, ID))
        elif len(elements) != 1:
            logger.info("Got {} element(s).".format(len(elements)))

        elem = elements[0]
        print("type(elem)=={}".format(type(elem)))
        return elem

    def setValueById(self, key, value):
        leaves = self._doc.getLeavesById(
            key, "text", "tspan", only_placeholders=False)
        # ^ FIXME: For some reason not all placeholders are
        #   detected, so only_placeholders=False is
        #   necessary.
        if not leaves:
            logger.warning("Missing {}".format(key))
            return
        for leaf in leaves:
            leaf.text = value
            value = ""  # Clear extra leaves to account for odd
            #  Inkscape behavior of generating multiple text tags
            #  for one visible text field

    def save(self, path=None, overwrite=False):
        """Save the xml.

        Args:
            path (str, optional): New path. Defaults to self._path.
            overwrite (bool, optional): Overwrite if exists.

        Raises:
            RuntimeError: If path was neither specified as an argument
                nor cached by the load method.
        """
        if path is None:
            path = self._path
        if not path:
            raise RuntimeError("path was neither loaded nor set manually.")

        return self._doc.render(path, overwrite=overwrite)



def main():
    print("running demo")
    MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
    REPO_DIR = os.path.dirname(MODULE_DIR)
    test_data_dir = os.path.join(REPO_DIR, "tests", "booktacular", "data")
    in_path = os.path.join(test_data_dir, "Nur_Wonderfield-pb2e.json")
    translate_path = os.path.join(test_data_dir, "sheet-fields.json")
    template_path = os.path.join(test_data_dir, "demo_sheet.svg")
    for path in (in_path, template_path):
        assert os.path.isfile(path), "Missing {}".format(repr(path))
    with open(translate_path, 'r') as stream:
        translators = json.load(stream)
    translator = translators['fill-and-delete-fields']
    sheet = BooktacularSheet()
    from booktacular.btpb2 import mappings
    sheet.load(template_path)
    sheet.set_mappings(mappings)
    sheet.set_meta(translator)
    with open(in_path, 'r') as stream:
        source = json.load(stream)
    sheet.set_values(source)
    # The text attribute itself has the id, so this should be easy:
    got_character_name_e = sheet.getElementById("character_name_")
    # got_id = got_character_name_e.attrib['id']  # "tspan1016"
    got_name = got_character_name_e.text
    good_name = "Nur Wonderfield"
    # If got_name is placeholder value, set_values must have failed:
    assert got_name == good_name, "%s != %s" % (got_name, good_name)
    # Harder to get since group has the id (ancestor g tag generated by
    #   Inkscape):
    got_ac_e = sheet.getElementById("armor_class_")
    got_ac_id = got_ac_e.attrib['id']  # tspan1020
    got_ac = got_ac_e.text  # can be integer
    good_ac = 17
    # If got_ac is placeholder value, set_values must have failed:
    assert int(got_ac) == good_ac, "%s != %s" % (got_ac, good_ac)
    new_path = os.path.splitext(template_path)[0] + ".FILLED.svg"
    if sheet.save(new_path, overwrite=True):
        print("Saved {}".format(repr(os.path.abspath(new_path))))
    else:
        print("Refusing to overwrite {}"
              .format(repr(os.path.abspath(new_path))))
    print("Example completed successfully.")


if __name__ == "__main__":
    sys.exit(main())