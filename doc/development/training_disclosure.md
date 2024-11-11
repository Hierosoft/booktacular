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

## booktacular

### morepdf
make a python script that accepts a "path", an "old" string and a "new" string, and replaces the old string with the new string assuming the path is a pdf

For backward compatibility, start with a python shebang and from __future__ import print_function, and use percent substitution instead of string interpolation throughout the code. Save the output file as os.path.splitext(path)[0] + "%s-.pdf" % new. Make replace_text_in_pdf a method of a new MorePDF class which has a "load" function to initialize doc which should become self.doc. Count the number of instances as in each block as block_replaced, then add that to a total "replaced" count, which should be shown in the print statement as "%s replacement(s) complete" instead of "Replacements complete". In save, rename "new" to "suffix" and only add "-%s" % suffix if suffix is not None. Call save like pdf_editor.save(path, suffix=new). use argparse. Instead of old, use args.find, and instead of new use args.replace. For find, allow -f or --find, for replace allow -r or --replace. If find is set and replace is not set, call replace_text_in_pdf(args.find, None). Change replace_text_in_pdf so that if new is None, the block's text is displayed with print but not modified. Display the page number before each matching block's text if new is None.


### moregeopandas
is there any way to make this geopandas program not overlap names when the points are near each other?
```
'''
Requires:
pip3 install pandas geopandas shapely pyarrow

"Pyarrow will become a required dependency of pandas in the next major
release of pandas (pandas 3.0), (to allow more performant data types,
such as the Arrow string type, and better interoperability with other
libraries)"
-pandas
'''
# import sys
import logging

# from collections import OrderedDict
# See <https://stackoverflow.com/a/53233489/4541104> (answered by Xiaoyu Lu)
import pandas as pd
from shapely.geometry import Point
import geopandas as gpd
from geopandas import GeoDataFrame
import matplotlib.pyplot as plt


from booktacular.irlmapping import (
    clean_coords,
)

logger = logging.getLogger(__name__)


def generate_map(waypoints_path):
    """Generate a map from a CSV file.
    The Zah Yest research CSV file has:
    Name for Campaign,Old Name (? for skip),ModernName,
    DescURL,LocationURL,AncientContinent,ModernCoords,LocationDesc,
    Description


    Args:
        waypoints_path (str): A CSV file with coordinates in various
            formats in the ModernCoords column.

    Raises:
        NotImplementedError: clean_coords returned an unexpected number
            of coords (expected 2 or 3).
    """
    # coords_path = "Long_Lats.csv"
    # with open(waypoints_path, 'r') as ins:
    coords_df = pd.read_csv(waypoints_path, delimiter=',', skiprows=0,
                            low_memory=False)
    # with open(coords_path, 'w') as outs:
    pairs = []
    longs = []
    lats = []
    cities = []
    names = []
    max = None
    skip = None
    count = 0
    for index, row in coords_df.iterrows():
        if max and len(cities) >= max:
            break
        _raw = row['ModernCoords']
        modern_name = row['ModernName']
        name = row['CustomName']
        old_name = row['OldName']
        if isinstance(old_name, str):
            if "(skip)" in old_name:
                print("* skipped OldName=\"{}\"".format(old_name))
                continue
        # if (not name) or (name == float('nan')):
        if not isinstance(name, str):
            print("* name={}({})=\"_____\"".format(type(name).__name__, name))
            name = "_____"
        else:
            print("* name={}({})".format(type(name).__name__, name))
        coords = None
        if not isinstance(_raw, str):
            # raise TypeError("Expected str got {}({})"
            #                 .format(type(coords).__name__, coords))
            logger.warning("  skipped ModernCoords={}({})"
                           .format(type(_raw).__name__, _raw))
            continue
        try:
            coords = clean_coords(_raw)
        except ValueError:
            logger.warning("  skipped ModernCoords=\"{}\"".format(_raw))
            continue
        # elevation = None
        if len(coords) == 3:
            # elevation = coords[2]
            coords = coords[:2]
        elif len(coords) != 2:
            raise NotImplementedError(
                "Expected 2 or 3 (N,E,[,elevation]) coords,"
                " got {}".format(coords))
        if skip is not None and count == skip:
            count += 1
            continue
        print("  {}={}".format(modern_name, coords))
        pairs.append(coords)
        lats.append(coords[0])
        longs.append(coords[1])
        cities.append(modern_name)
        names.append(name)
        count += 1
    # return 0
    # coords_df.insert(0, 'Longitude', longs, True)
    # coords_df.insert(1, 'Latitude', lats, True)
    # coords_df = pd.DataFrame(lists)
    # coords_df.to_csv(coords_path, index=False)

    # Fields: See docstring.
    coords_df = pd.DataFrame({
        # "Name": names,
        "Name": cities,
        "Latitude": lats,
        "Longitude": longs,
    })

    # coords_df = pd.read_csv(coords_path, delimiter=',', skiprows=0,
    #   low_memory=False)

    # geometry = \
    # [Point(xy) for xy in zip(coords_df['Longitude'], coords_df['Latitude'])]
    geometry = [Point(xy) for xy in zip(longs, lats)]  # switch them!
    gdf = GeoDataFrame(coords_df, geometry=geometry)

    # this is a simple map that goes with geopandas
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    result = gdf.plot(ax=world.plot(figsize=(10, 6)), marker='o', color='red',
                      markersize=15)
    for idx, dat in coords_df.iterrows():
        # print(dat.city, dat.lng, dat.lat)
        # result.scatter(dat.Longitude, dat.Latitude, s=10, color='red')
        result.annotate(dat.Name, (dat.Longitude, dat.Latitude))

    plt.show()
```

It has "AttributeError: The geopandas.dataset has been deprecated and was removed in GeoPandas 1.0. You can get the original 'naturalearth_lowres' data from https://www.naturalearthdata.com/downloads/110m-cultural-vectors/". If it doesn't exist in the current working directory path = os.path.join(os.getcwd(), "ne_110m_admin_0_countries.zip"), download url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
then download it if doesn't exist then
```
gdf = gpd.read_file(path)

For compatibility, do it with urrlib and import it like this:
if sys.version_info.major >= 3:
    import urllib.request
    request = urllib.request
    from urllib.error import (
        HTTPError,
        URLError,
    )
    from urllib.parse import urlparse, parse_qs
    from urllib.parse import quote as urllib_quote
    from urllib.parse import quote_plus as urllib_quote_plus
    from urllib.parse import urlencode
else:
    # Python 2
    import urllib2 as urllib  # type: ignore
    request = urllib
    from urllib2 import (  # type: ignore
        HTTPError,
        URLError,
    )
    from HTMLParser import HTMLParser  # noqa: F401 # type: ignore
    print("HTMLParser imported.", file=sys.stderr)
    from urlparse import urlparse, parse_qs  # noqa: F401 # type: ignore
    from urllib import quote as urllib_quote  # noqa: F401 # type: ignore
    from urllib import quote_plus as urllib_quote_plus  # noqa: F401,E501 # type: ignore
    from urllib import urlencode  # noqa: F401 # type: ignore
```
