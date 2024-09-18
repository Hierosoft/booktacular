from collections import OrderedDict
import csv
import json
import os
import sys

from logging import getLogger

from pyinkscape import (
    Canvas,
)

if __name__ == "__main__":
    MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.dirname(MODULE_DIR))

from booktacular import (
    get_all_queries,
    query_dict,
)

from pyinkscape.xmlnav import (
    # clean_el_repr,
    # used_element,
    # get_leaf,
    used_elements,
    # SVG_NS,
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
    """Manage sheet filling.
    Attributes:
        _mappingsPath (str): The mappings CSV path that maps Source
            (JSON xpath) to destination (SVG ID). See loadMappings
            and loadFields.
        _path (str): The SVG template path.
        results (dict): Results of the last loadSheet or fillSheet
            fed to saveMappings to see what fields were and weren't
            mapped using a csv file that can be then edited to map more
            Source (JSON xpath) and Destination (SVG ID) fields.
    """
    def __init__(self):
        self._doc = None
        self._path = None
        self._meta = None
        self._mappings = None
        self.results = None
        self._mappingsPath = None
        self._sourceData = None

    def load(self, path):
        self._doc = Canvas(path)
        self._path = path

    def setMeta(self, meta):
        """Set the SVG's usage metadata for fields by name.
        The structure is used as a translator.
        Example: e1p-character-sheet-for-pf2/character-fields.json
        """
        self._meta = meta

    def setMappings(self, mappings):
        """Set dict that maps data json paths to SVG field names
        Example: from booktacular.btpb2 import mappings
        """
        # TODO: Do this automatically. See for location.
        self._mappings = mappings

    def emitFillResultsYaml(self):
        if not self.results:
            return {
                'error': "There are no results. Run setFields first."
            }
        # shown_keys = set()
        results = self.results
        shown_sub_keys = set()
        ordered_keys = ['used_dst_keys', 'used_src_keys',
                        'unused_src_keys', 'unused_dst_keys']
        # ^ Show these first since more meaningful than showing
        #   the keys as src_keys or dst_keys and shown_keys
        #   makes keys only show one time.

        for key in results.keys():
            if key not in ordered_keys:
                ordered_keys.append(key)

        variable_keys = []
        print("results:")
        for key in ordered_keys:
            result = results[key]
            # shown_keys.add(key)
            if result:
                print(f"  {key}:")
                if isinstance(result, (list, tuple, set)):
                    for sub_key in result:
                        if sub_key in shown_sub_keys:
                            continue
                        shown_sub_keys.add(sub_key)
                        print(f"  - \"{sub_key}\"")
                elif hasattr(result, 'items'):  # usually dict or OrderedDict
                    for sub_key, value in result.items():
                        if sub_key in shown_sub_keys:
                            continue
                        shown_sub_keys.add(sub_key)
                        print(f"    {sub_key}: \"{value}\"")
                else:
                    variable_keys.add(key)

        for key in variable_keys:
            # Do this separately since str is probably important (msg, error, etc)
            print(f"  {key}: \"{results[key]}\"")

    def mappingsPath(self):
        return self._mappingsPath

    def setMappingsPath(self, value):
        self._mappingsPath = value

    def saveMappings(self, data: dict, path: str = None) -> None:
        """Save the provided dictionary data to a CSV file.

        Args:
            data (dict): A dictionary containing 'src_keys' (list of
                source keys), 'dst_keys' (list of destination keys), and
                'mapped' (sub dictionary).
            path (str, optional): The file path where the CSV file will
                be saved. Defaults to self.mappingsPath().

        Raises:
            ValueError: If the path is not provided nor is
                mappingsPath() a path.
        """
        # Default to self.mappingsPath() if path is None
        if path is None:
            path = self.mappingsPath()

        if path is None:
            raise ValueError(
                "File path must be provided,"
                " otherwise call setMappingsPath first.")
        if self._sourceData is None:
            raise ValueError(
                "You must call loadFields or setFields before saveMappings.")

        with open(path, mode='w', newline='') as file:
            writer = csv.writer(file)

            # Write the title row
            writer.writerow(["Source", "Value", "Destination"])

            # Write the mapped dictionary's key-value pairs
            for xpath, dst in data['mapped'].items():
                new = query_dict(self._sourceData, xpath)
                writer.writerow([xpath, new, dst])

            # Write each src_key with an empty destination
            for xpath in data['src_keys']:
                if xpath not in data['mapped']:
                    new = query_dict(self._sourceData, xpath)
                    writer.writerow([xpath, new, ""])

            # Write each dst_key with an empty source
            for dst_key in data['dst_keys']:
                if dst_key not in data['mapped'].values():
                    writer.writerow(["", "", dst_key])
            print("Saved '{}' (used and unused mappings)".format(path))

    def loadMappings(self, path: str) -> None:
        """Load mappings from a CSV file into the self._mappings OrderedDict.

        Args:
            path (str): The file path from where the CSV file will be loaded.

        Raises:
            ValueError: If the Source or Destination columns are not found in the CSV.
        """
        mappings = OrderedDict()

        with open(path, mode='r', newline='') as file:
            reader = csv.reader(file)

            # Read the title row and determine the indices for Source and Destination
            header = next(reader)

            try:
                src_idx = header.index("Source")
                dst_idx = header.index("Destination")
            except ValueError:
                raise ValueError(
                    "CSV must contain 'Source' (xpath-style json path)"
                    " and 'Destination (SVG element ID)' columns.")

            # Iterate over the remaining rows
            for row in reader:
                src = row[src_idx].strip() if row[src_idx] else None
                dst = row[dst_idx].strip() if row[dst_idx] else None

                if src and dst:
                    mappings[src] = dst

        # Append the loaded mappings to self._mappings
        if not hasattr(self, '_mappings'):
            self._mappings = OrderedDict()

        self._mappings.update(mappings)

    def loadFields(self, data_path):
        self._in_path = data_path
        mappings_csv_path = os.path.splitext(data_path)[0]
        mappings_csv_path += ".booktacular-mappings.csv"
        self.setMappingsPath(mappings_csv_path)
        with open(data_path, 'r') as stream:
            source_data = json.load(stream)
        return self.setFields(source_data)

    def setFields(self, source_data):
        """Set all of the values possible in SVG from source
        Uses meta (a.k.a. translator)

        self._meta Example: e1p-character-sheet-for-pf2/character-fields.json

        self._mappings Example: from booktacular.btpb2 import mappings

        Args:
            data (dict): Character data, such as representing a JSON
                file exported by PB2e
        """
        if not hasattr(self._doc, "setField"):
            raise TypeError(
                f"_doc is {type(self._doc)} but is missing .setField"
                " (expected Canvas from Hierosoft fork of pyinkscape)")
        if self._mappingsPath:
            self.loadMappings(self._mappingsPath)
        else:
            print(
                "Warning: not loaded from file."
                " No mappings CSV file will be loaded"
                " and missing ones will not save."
                " To avoid this, use loadFields"
                " instead of setFields, or call setMappingsPath"
                " before calling setFields.")
        self._sourceData = source_data
        results = {
            "missing_source_fields": [],
            "missing_template_fields": [],
        }
        no_dst_key = set()
        no_src_key = set()
        results['dst_keys'] = set()
        # results['used_src_keys'] = set()  # replaced by 'mapped'
        results['src_keys'] = get_all_queries(source_data)
        # results['used_dst_keys'] = set()  # replaced by 'mapped'
        results['mapped'] = OrderedDict()
        if no_dst_key:
            logger.warning("Source fields with no destination field:"
                           f" {no_dst_key}")
        if no_src_key:
            logger.warning("Destination fields with no source field:"
                           f" {no_src_key}")
        all_dst_keys = self._doc.getAllIds()
        for key in all_dst_keys:
            if key.endswith("_"):
                results['dst_keys'].add(key)
        # results['used_src_keys'] = []  # See results['mapped'] keys
        results['used_dst_keys'] = set()  # may be bigger than
        #   results['mapped'] if there is a problem.
        for xpath, field in self._mappings.items():
            new = query_dict(source_data, xpath)
            if new is None:
                results['missing_source_fields'].append(xpath)
                msg = f"data source is missing {xpath}"
                logger.warning(msg)
                continue
            # leaves = self._doc.setField(
            #     field, "text", "tspan", skip_empty=False)
            # ^ FIXME: For some reason not all placeholders are
            #   detected, so skip_empty=False is
            #   necessary. Therefore, set value on
            #   first non-empty one below.
            # if not leaves:
            if not self._doc.setField(field, str(new)):
                results['missing_template_fields'].append(xpath)
                msg = (f"sheet is missing text or group"
                       f" with id={repr(xpath)} containing a tspan")
                logger.warning(msg)
                continue
            # results['used_src_keys'].add(xpath)
            # results['used_dst_keys'].add(field)
            if field in results['used_dst_keys']:
                print("Warning: changing source field {}"
                      " mapping destination from {} to {}"
                      .format(xpath, results['mapped'][xpath], field))
            results['mapped'][xpath] = field
        results['used_dst_keys'] = results['mapped'].values()
        # ^ values is the real set of used values, since could be
        #   redundant!

        results['used_src_keys'] = list(results['mapped'].keys())
        for origin in ('src', 'dst'):
            origin_keys = f'{origin}_keys'
            unused_origin_keys = f'unused_{origin}_keys'
            # ^ defines unused_dst_keys and unused_src_keys
            used_origin_keys = f'used_{origin}_keys'
            results[unused_origin_keys] = set()
            for key in results[origin_keys]:
                if key not in results[used_origin_keys]:
                    # If this key in src_keys not in used_src_keys,
                    #   add it to unused_src_keys
                    results[unused_origin_keys].add(key)
        del results['used_src_keys']  # see mapped instead

        self.results = results
        self.saveMappings(results)
        return results

    def getContent(self, ID):
        # formerly getValueById
        self._doc.setField()
        # leaves = self._doc.getLeavesById(
        #     ID, "text", "tspan", skip_empty=True)
        # if not leaves:
        #     return None
        # if len(leaves) > 1:
        #     used = used_elements(leaves)
        #     return used[0]
        # return leaves[0].text

    def getElementById(self, ID):
        # get all existing layers
        # layers = self._doc.layers()
        # # get a layer by name
        # layer1 = self._doc.layer("Layer 1")
        # # get a layer by ID
        # layer1 = self._doc.layer_by_id("layer1")
        return self._doc.getElementById(ID)
        # elements = self._doc.getLeavesById(
        #     ID, "text", "tspan", skip_empty=True)
        # if len(elements) < 1:
        #     raise ValueError("{} is missing id {}".format(self._path, ID))
        # elif len(elements) != 1:
        #     logger.info("Got {} element(s).".format(len(elements)))

        # elem = elements[0]
        # print("type(elem)=={}".format(type(elem)))
        # return elem

    def setValueById(self, key, value):
        return self._doc.setField(key, value)
        # leaves = self._doc.getLeavesById(
        #     key, "text", "tspan", skip_empty=False)
        # # ^ FIXME: For some reason not all placeholders are
        # #   detected, so skip_empty=False is
        # #   necessary.
        # if not leaves:
        #     logger.warning("Missing {}".format(key))
        #     return
        # for leaf in leaves:
        #     leaf.text = value
        #     value = ""  # Clear extra leaves to account for odd
        #     #  Inkscape behavior of generating multiple text tags
        #     #  for one visible text field

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
    sheet.setMappings(mappings)
    sheet.setMeta(translator)
    with open(in_path, 'r') as stream:
        source = json.load(stream)
    sheet.setFields(source)
    # The text attribute itself has the id, so this should be easy:
    got_character_name_e = sheet.getElementById("character_name_")
    # got_id = got_character_name_e.attrib['id']  # "tspan1016"
    got_name = got_character_name_e.text
    good_name = "Nur Wonderfield"
    # If got_name is placeholder value, setFields must have failed:
    assert got_name == good_name, "%s != %s" % (got_name, good_name)
    # Harder to get since group has the id (ancestor g tag generated by
    #   Inkscape):
    got_ac_e = sheet.getElementById("armor_class_")
    got_ac_id = got_ac_e.attrib['id']  # tspan1020
    got_ac = got_ac_e.text  # can be integer
    good_ac = 17
    # If got_ac is placeholder value, setFields must have failed:
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