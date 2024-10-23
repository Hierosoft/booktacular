# LLM Disclosure for {{ project }}
This LLM Disclosure, which may be more specifically titled above here (and in this document possibly referred to as "this document"), is based on the LLM Disclosure at https://github.com/Hierosoft/llm-disclosure by Jake Gustafson. Jake Gustafson is probably *not* an author of the project unless listed as a project author, nor necessarily the editor of this copy of the document unless this copy is the original which among other places I, Jake Gustafson, state IANAL clearly and publicly. This LLM Disclosure is released under the [CC0](https://creativecommons.org/public-domain/cc0/) license.

Document editor: {{ organization }}

This document is a voluntary of how and where content in or used by this project was produced by LLM(s) or any tools that are "trained" in any way.

The main section of this document lists such tools. For each, the version, install location, and a scope of their training sources in a way that is specific as possible.

Subsections of this document contain prompts used to generate content, in a way that is complete to the best ability of the document editor.

tool(s) used:
- GPT-4-Turbo, version 4o (chatgpt.com)

Scope of use: Code where listed in this document, but all resulting code had to be co-written by Jake Gustafson such as:
- for correct docstrings
- to fix logic
- to integrate with existing code

Project Authors: See Readme, license, code comments, etc.

## SheetFiller
### BooktacularSheet
#### saveMapping
- September 14, 2024

Create a python method that takes a path where to save a csv file and a dictionary with 3 entries: 2 lists and a sub dict. The lists are stored in the keys 'src_keys', 'dst_keys', and sub dict in 'mapped'. Store ["Source", "Destination"] in the title row. Write the entire dictionary's key, value pairs as rows. Then for each src_key in src_keys write [src_key, ""], then for each dst_key in dst_keys write ["", dst_key]. Save the csv file to path.

make the path string second, make it optional and default to None

Rename the method to saveMappings. If the value turns out to be None, set it to self.mappingsPath(). in the docstring say "Defaults to self.mappingsPath()". If it is still None after that, then raise the error.

Now write a loadMappings(path) method that will load a CSV file with those columns and store the Source and Destination columns as key, value pairs in mappings = OrderedDict(). Remember to read the first row separately as the title row and determine which column is Source and which is Destination, then use those column indices throughout the method for reading Source's as key and Destination's as value. Then after iteration of all rows is complete, append that dict to the self._mappings OrderedDict().


## morepdf
make a python script that accepts a "path", an "old" string and a "new" string, and replaces the old string with the new string assuming the path is a pdf

For backward compatibility, start with a python shebang and from __future__ import print_function, and use percent substitution instead of string interpolation throughout the code. Save the output file as os.path.splitext(path)[0] + "%s-.pdf" % new. Make replace_text_in_pdf a method of a new MorePDF class which has a "load" function to initialize doc which should become self.doc. Count the number of instances as in each block as block_replaced, then add that to a total "replaced" count, which should be shown in the print statement as "%s replacement(s) complete" instead of "Replacements complete". In save, rename "new" to "suffix" and only add "-%s" % suffix if suffix is not None. Call save like pdf_editor.save(path, suffix=new). use argparse. Instead of old, use args.find, and instead of new use args.replace. For find, allow -f or --find, for replace allow -r or --replace. If find is set and replace is not set, call replace_text_in_pdf(args.find, None). Change replace_text_in_pdf so that if new is None, the block's text is displayed with print but not modified. Display the page number before each matching block's text if new is None.
