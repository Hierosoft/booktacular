
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
SVG_NAMESPACES = {'ns': SVG_NS,
          'svg': SVG_NS,
          'dc': "http://purl.org/dc/elements/1.1/",
          'cc': "http://creativecommons.org/ns#",
          'rdf': "http://www.w3.org/1999/02/22-rdf-syntax-ns#",

          "sodipodi": "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
          'inkscape': INKSCAPE_NS}

data1 = """
<root>
    <text type="news">This is the text news.</text>
    <articles>
        <article type="info">
             <content>some text</content>
        </article>
        <article type="info">
             <content>some text</content>
        </article>
        <article type="info">
             <content>some text</content>
        </article>
    </articles>
</root>
"""


data2 = """
<root>
    <articles>
        <article type="news">
             <content>This is the article news.</content>
        </article>
        <article type="info">
             <content>some text</content>
        </article>
        <article type="news">
             <content>some text</content>
        </article>
    </articles>
</root>
"""

# root1 = etree.fromstring(data1)
# root2 = etree.fromstring(data2)

# for this_root in (root1, root2):
for data in (data1, data2):
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

    # print(this_root.xpath("//article[@type='news']/content/text()"))
    query_string = "//article[@type='news']/content"
    # FIXME: ^ gets 0 elements from data1.
    namespaces=SVG_NAMESPACES
    if _LXML_AVAILABLE:
        elements = __root.xpath(query_string, namespaces=namespaces)
    else:
        elements = __tree.findall(query_string, namespaces=namespaces)
    print("got {} element(s)".format(len(elements)))
    for elem in elements:
        raise NotImplementedError(
            "{}({}); dir(elem)=={}"
            .format(type(elem), elem, dir(elem)))
