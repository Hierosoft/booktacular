import os
import sys

from logging import getLogger

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

    def load(path):
        pass

    def setValueById(self, name, value):
        pass

    def save(self, path=None):
        if path is None:
            path = self._path
        if not path:
            raise RuntimeError("path was neither loaded nor set manually.")

