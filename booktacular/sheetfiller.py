

FIELD_META_KEYS = [
    "tip", "value_line_style_template", "choices",
    "deletes", "append_variable", "prefix", "suffix",
    "base_attribute_", "rules", "default",
    "recommended_max_characters", "max_characters",
    "lines", "lambda", "value_deletes", "value_properties",
    "delete_if_not", "keep"]
# TODO: implement globals (such as those used by delete_if_not, and others starting with _)
# TODO: if keep, keep initial value in sheet unless set (or deleted by a condition)
RULES_META_KEYS = ["lambdas"]
LAMBDA_OPERATORS = ["+"]
LAMBDA_FUNCTIONS = ["min"]

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
