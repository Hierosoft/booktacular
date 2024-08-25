"""
Query string example.
This can be changed to try different xpath queries.

Expected output:
got 2 element(s)
text=None
text=Mr. Rogers
got 1 element(s)
text=Mr. Rogers

The first None is expected due to an empty tspan
(which Inkscape commonly generates)
"""
from io import StringIO

# mimic pyinkscape:
import os
import logging
import math
import warnings
from pathlib import Path
try:
    from lxml import etree
    from lxml.etree import XMLParser
    _LXML_AVAILABLE = True
except Exception as e:
    # logging.getLogger(__name__).debug("lxml is not available, fall back to xml.etree.ElementTree")
    from xml.etree import ElementTree as etree
    from xml.etree.ElementTree import XMLParser
    _LXML_AVAILABLE = False

INKSCAPE_NS = 'http://www.inkscape.org/namespaces/inkscape'
SVG_NS = 'http://www.w3.org/2000/svg'
SVG_NAMESPACES = {
    'ns': SVG_NS,
    'svg': SVG_NS,
    'dc': "http://purl.org/dc/elements/1.1/",
    'cc': "http://creativecommons.org/ns#",
    'rdf': "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "sodipodi": "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
    'inkscape': INKSCAPE_NS
}

data1 = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!-- Created with Inkscape (http://www.inkscape.org/) -->

<svg
   width="8.5in"
   height="11in"
   viewBox="0 0 215.9 279.4"
   version="1.1"
   id="svg5"
   inkscape:version="1.1.2 (0a00cf5339, 2022-02-04)"
   sodipodi:docname="demo_sheet.svg"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
   xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:svg="http://www.w3.org/2000/svg">
  <sodipodi:namedview
     id="namedview7"
     pagecolor="#ffffff"
     bordercolor="#666666"
     borderopacity="1.0"
     inkscape:pageshadow="2"
     inkscape:pageopacity="0.0"
     inkscape:pagecheckerboard="0"
     inkscape:document-units="mm"
     showgrid="false"
     inkscape:zoom="0.24943883"
     inkscape:cx="296.66592"
     inkscape:cy="200.44995"
     inkscape:window-width="1051"
     inkscape:window-height="544"
     inkscape:window-x="176"
     inkscape:window-y="104"
     inkscape:window-maximized="0"
     inkscape:current-layer="layer1"
     units="in" />
    <g>
      <text id="character_name_"><tspan></tspan><tspan>Mr. Rogers</tspan></text>
    </g>
    <g>
        <article id="info1">
             <content>some text</content>
        </article>
        <article id="info2">
             <content>some text</content>
        </article>
        <article id="info3">
             <content>some text</content>
        </article>
    </g>
</svg>
"""


data2 = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!-- Created with Inkscape (http://www.inkscape.org/) -->

<svg
   width="8.5in"
   height="11in"
   viewBox="0 0 215.9 279.4"
   version="1.1"
   id="svg5"
   inkscape:version="1.1.2 (0a00cf5339, 2022-02-04)"
   sodipodi:docname="demo_sheet.svg"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
   xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:svg="http://www.w3.org/2000/svg">
  <sodipodi:namedview
     id="namedview7"
     pagecolor="#ffffff"
     bordercolor="#666666"
     borderopacity="1.0"
     inkscape:pageshadow="2"
     inkscape:pageopacity="0.0"
     inkscape:pagecheckerboard="0"
     inkscape:document-units="mm"
     showgrid="false"
     inkscape:zoom="0.24943883"
     inkscape:cx="296.66592"
     inkscape:cy="200.44995"
     inkscape:window-width="1051"
     inkscape:window-height="544"
     inkscape:window-x="176"
     inkscape:window-y="104"
     inkscape:window-maximized="0"
     inkscape:current-layer="layer1"
     units="in" />
    <g>
      <g>
        <text id="character_name_">
             <tspan>Mr. Rogers</tspan>
        </text>
        <article id="info1">
             <content>some text</content>
        </article>
        <article id="news2">
             <content>some text</content>
        </article>
      </g>
    </g>
</svg>
"""

data3 = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!-- Created with Inkscape (http://www.inkscape.org/) -->

<svg
   width="8.5in"
   height="11in"
   viewBox="0 0 215.9 279.4"
   version="1.1"
   id="svg5"
   inkscape:version="1.1.2 (0a00cf5339, 2022-02-04)"
   sodipodi:docname="demo_sheet.svg"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
   xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:svg="http://www.w3.org/2000/svg">
  <sodipodi:namedview
     id="namedview7"
     pagecolor="#ffffff"
     bordercolor="#666666"
     borderopacity="1.0"
     inkscape:pageshadow="2"
     inkscape:pageopacity="0.0"
     inkscape:pagecheckerboard="0"
     inkscape:document-units="mm"
     showgrid="false"
     inkscape:zoom="0.24943883"
     inkscape:cx="296.66592"
     inkscape:cy="200.44995"
     inkscape:window-width="1051"
     inkscape:window-height="544"
     inkscape:window-x="176"
     inkscape:window-y="104"
     inkscape:window-maximized="0"
     inkscape:current-layer="layer1"
     units="in" />
    <g id="character_name_">
      <g>
        <text id="text1">
             <tspan>Mr. Rogers</tspan>
        </text>
        <article id="info1">
             <content>some text</content>
        </article>
        <article id="news2">
             <content>some text</content>
        </article>
      </g>
    </g>
</svg>
"""
sheet_path = os.path.realpath("../../../tests/booktacular/data/demo_sheet.svg")
if os.path.isfile("tests/booktacular/data/demo_sheet.svg"):
    sheet_path = os.path.realpath("tests/booktacular/data/demo_sheet.svg")
with open(sheet_path) as stream:
    data4 = stream.read()

# root1 = etree.fromstring(data1)
# root2 = etree.fromstring(data2)

# for this_root in (root1, root2):
for i, data in enumerate([data1, data2, data3, data4]):
    number = i + 1
    # mimic pyinkscape:
    remove_blank_text = True
    encoding = "utf-8"
    kwargs = {'encoding': encoding}
    if _LXML_AVAILABLE:
        kwargs['remove_blank_text'] = remove_blank_text  # this flag is lxml specific
    this_root = None
    with StringIO(data) as infile:
        parser = XMLParser(**kwargs)
        __tree = etree.parse(infile, parser)
        __root = __tree.getroot()

    # print(this_root.xpath("//article[@id='news']/content/text()"))
    # query_string = "/ns:svg/ns:g/ns:text[@id='character_name_']/ns:tspan"
    # ^ assumes direct descendant, so add extra slash:
    # query_string = "/ns:svg/ns:g//ns:text[@id='character_name_']//ns:tspan"
    # ^ still no results, so:

    # query_string = ".//svg:text[@id='character_name_']/svg:tspan"
    # ^ FutureWarning: This search is broken in 1.3 and earlier, and
    #   will be fixed in a future version.  If you rely on the current
    #   behaviour, change it to
    #   ".//svg:text[@id='character_name_']/svg:tspan"
    print()
    tag = "text"
    id = "character_name_"
    if number == 4:
        id = "armor_class_"
    query_string = ".//svg:text[@id='{}']/svg:tspan".format(id)
    # query_string = ".//svg:text[@id='character_name_']//svg:tspan"
    # Namespaces Handling: The SVG document uses a default namespace,
    #   http://www.w3.org/2000/svg. In XPath queries, elements in this
    #   namespace need to be prefixed with the namespace prefix, which is
    #   defined as 'svg' in the SVG_NAMESPACES dictionary.
    # XPath Query: The query string query_string =
    #   ".//svg:text[@id='character_name_']/svg:tspan" correctly includes
    #   the namespace prefix (svg:), ensuring that the XPath engine
    #   knows to look for elements in the http://www.w3.org/2000/svg
    #   namespace.
    namespaces = SVG_NAMESPACES
    if _LXML_AVAILABLE:
        elements = __root.xpath(query_string, namespaces=namespaces)
    else:
        elements = __tree.findall(query_string, namespaces=namespaces)
    if len(elements) == 0:
        tag = "g"
        query_string = ".//svg:g[@id='{}']//svg:tspan".format(id)
        # ^ // allows indirect descendants
        if _LXML_AVAILABLE:
            elements = __root.xpath(query_string, namespaces=namespaces)
        else:
            elements = __tree.findall(query_string, namespaces=namespaces)

    print("got {} {} element(s)".format(tag, len(elements)))
    for el in elements:
        # raise NotImplementedError(
        #     "{}({}); dir(el)=={}"
        #     .format(type(el), el, dir(el)))
        # ^ append, attrib, clear, extend, find, findall, findtext
        #   get, getchildren, getiterator, insert, items, iter,
        #   iterfind, itertext, keys, makeelement, remove, set,
        #   tag, tail, text
        print("text={}".format(el.text))
        print("getchildren()=={}".format(el.getchildren()))
