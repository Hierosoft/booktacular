# -*- coding: utf-8 -*-
"""
Created on Sun Dec 4, 2022

@author: Jake "Poikilos" Gustafson
"""
import unittest
import sys
import os

from collections import OrderedDict
from pprint import pformat


test_sgml_data = '''        <PAGEOBJECT XPOS="766.0008" YPOS="30026.5978352942" OwnPage="72" ItemID="1378889691" PTYPE="2" WIDTH="522" HEIGHT="519.482352941148" FRTYPE="0" CLIPEDIT="0" PWIDTH="1" PLINEART="1" LOCALSCX="0.24" LOCALSCY="0.24" LOCALX="0" LOCALY="0" LOCALROT="0" PICART="1" SCALETYPE="1" RATIO="1" Pagenumber="0" PFILE="images/the_pyramid_and_mercury_mines_entrances.png" IRENDER="0" EMBEDDED="0" path="M0 0 L522 0 L522 519.482 L0 519.482 L0 0 Z" copath="M0 0 L522 0 L522 519.482 L0 519.482 L0 0 Z" gXpos="766.0008" gYpos="30026.5978352942" gWidth="0" gHeight="0" LAYER="0" NEXTITEM="-1" BACKITEM="-1"/>
        <PAGEOBJECT XPOS="136.0008" YPOS="30840.12" OwnPage="73" ItemID="1378880123" PTYPE="4" WIDTH="522" HEIGHT="28.7999999999811" FRTYPE="0" CLIPEDIT="0" PWIDTH="1" PLINEART="1" LOCALSCX="1" LOCALSCY="1" LOCALX="0" LOCALY="0" LOCALROT="0" PICART="1" SCALETYPE="1" RATIO="1" COLUMNS="1" COLGAP="0" AUTOTEXT="0" EXTRA="0" TEXTRA="0" BEXTRA="0" REXTRA="0" VAlign="0" FLOP="0" PLTSHOW="0" BASEOF="0" textPathType="0" textPathFlipped="0" path="M0 0 L522 0 L522 28.8 L0 28.8 L0 0 Z" copath="M0 0 L522 0 L522 28.8 L0 28.8 L0 0 Z" gXpos="608" gYpos="14140.0544" gWidth="0" gHeight="0" LAYER="0" NEXTITEM="-1" BACKITEM="-1">
            <StoryText>
                <DefaultStyle/>
                <ITEXT CH="The Pyramid - Inside"/>
                <para PARENT="Place Name - major - H1"/>
            </StoryText>
            <PageItemAttributes>
                <ItemAttribute Name="TOC" Type="none" Value="      The Pyramid - Inside" Parameter="" Relationship="none" RelationshipTo="" AutoAddTo="none"/>
            </PageItemAttributes>
        </PAGEOBJECT>'''

my_dir = os.path.dirname(os.path.abspath(__file__))
module_dir = os.path.dirname(my_dir)
repo_dir = os.path.dirname(module_dir)

if __name__ == "__main__":
    sys.path.insert(0, repo_dir)

from tabletopper.morescribus import (  # noqa: E402
    SGMLLexer,
    # from_string,
    from_string_scribus,
    # SGMLElementTree,
    # SGMLNode,
    # SGMLText,
)


def echo0(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


spaced_xml_data = """<?xml version="1.0" encoding="UTF-8"?>
<SCRIBUSUTF8NEW Version="1.5.8">
    <DOCUMENT ANZPAGES="168">
        <PAGEOBJECT XPOS="766.0008" YPOS="1720.008" OwnPage="1">
            <StoryText>
                <DefaultStyle/>
                <ITEXT CH="The print edition has a graphical cover. "/>
            </StoryText>
        </PAGEOBJECT>
    </DOCUMENT>
</SCRIBUSUTF8NEW>
"""
xml_data = (  # NO .value (no content, not even whitespace nor newlines)
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<SCRIBUSUTF8NEW Version="1.5.8">'
    '<DOCUMENT ANZPAGES="168">'
    '<PAGEOBJECT XPOS="766.0008" YPOS="1720.008" OwnPage="1">'
    '<StoryText>'
    '<DefaultStyle/>'
    '<ITEXT CH="The print edition has a graphical cover. "/>'
    '</StoryText>'
    '</PAGEOBJECT>'
    '</DOCUMENT>'
    '</SCRIBUSUTF8NEW>'
)
DOCTYPE = OrderedDict()
SCRIBUSUTF8NEW = OrderedDict()
xml_data_dict = OrderedDict()
xml_data_dict['tagName'] = None  # Since it is the document itself
xml_data_dict['attributes'] = OrderedDict()
xml_data_dict['children'] = [
    DOCTYPE,
    SCRIBUSUTF8NEW,
]
DOCTYPE['context'] = SGMLLexer.START
DOCTYPE['tagName'] = "?xml"
DOCTYPE['attributes'] = OrderedDict()
DOCTYPE['attributes']['version'] = "1.0"
DOCTYPE['attributes']['encoding'] = "UTF-8"
DOCTYPE['self_closer'] = "?"
# ^ Scribus-style SGML (not XML)

DOCUMENT = OrderedDict()

SCRIBUSUTF8NEW['context'] = SGMLLexer.START
SCRIBUSUTF8NEW['tagName'] = "SCRIBUSUTF8NEW"
SCRIBUSUTF8NEW['attributes'] = OrderedDict()
SCRIBUSUTF8NEW['attributes']['Version'] = "1.5.8"
SCRIBUSUTF8NEW['children'] = [
    DOCUMENT,
]

PAGEOBJECT = OrderedDict()

DOCUMENT['context'] = SGMLLexer.START
DOCUMENT['tagName'] = "DOCUMENT"
DOCUMENT['attributes'] = OrderedDict()
DOCUMENT['attributes']['ANZPAGES'] = "168"
DOCUMENT['children'] = [
    PAGEOBJECT,
]

StoryText = OrderedDict()

PAGEOBJECT['context'] = SGMLLexer.START
PAGEOBJECT['tagName'] = "PAGEOBJECT"
PAGEOBJECT['attributes'] = OrderedDict()
PAGEOBJECT['attributes']['XPOS'] = "766.0008"
PAGEOBJECT['attributes']['YPOS'] = "1720.008"
PAGEOBJECT['attributes']['OwnPage'] = "1"
PAGEOBJECT['children'] = [
    StoryText,
]

DefaultStyle = OrderedDict()
ITEXT = OrderedDict()

StoryText['context'] = SGMLLexer.START
StoryText['tagName'] = "StoryText"
StoryText['attributes'] = OrderedDict()
StoryText['children'] = [
    DefaultStyle,
    ITEXT,
]

DefaultStyle['context'] = SGMLLexer.START
DefaultStyle['tagName'] = "DefaultStyle"
DefaultStyle['attributes'] = OrderedDict()
DefaultStyle['self_closer'] = "/"

ITEXT['context'] = SGMLLexer.START
ITEXT['tagName'] = "ITEXT"
ITEXT['attributes'] = OrderedDict()
ITEXT['attributes']['CH'] = "The print edition has a graphical cover. "
ITEXT['self_closer'] = "/"

# NOTE: OwnPage="-1" *is* valid in Scribus project file!


class TestMoreScribus(unittest.TestCase):

    def assertAllEqual(self, list1, list2, tbs=None):
        '''
        [copied from pycodetools.parsing by author]
        '''
        if len(list1) != len(list2):
            echo0("The lists are not the same length: list1={}"
                  " and list2={}".format(list1, list2))
            self.assertEqual(len(list1), len(list2))
        for i in range(len(list1)):
            try:
                self.assertEqual(list1[i], list2[i])
            except AssertionError as ex:
                if tbs is not None:
                    echo0("reason string (tbs): " + tbs)
                raise ex

    def test_properties(self):
        sgml = SGMLLexer(test_sgml_data)
        pfile_found = False
        for chunkdef in sgml:
            chunk = sgml.chunk_from_chunkdef(chunkdef)
            if chunkdef.get('tagName') is None:
                continue
            if chunkdef.get('attributes') is None:
                # It is a closing tag.
                continue
            pfile = chunkdef['attributes'].get('PFILE')
            if pfile is not None:
                pfile_found = True
                self.assertEqual(
                    pfile,
                    "images/the_pyramid_and_mercury_mines_entrances.png",
                )
        self.assertTrue(pfile_found)

    def assertMoreEqual(self, d1, d2, key=None):
        """Show the difference without elipsis.

        The superclass' assertEqual skips details in big dicts. For example:
        `AssertionError: Order[612 chars]008'), ('OwnPage', '1')])),
        ('children', [Orde[399 chars])])]) != Order[612 chars]008')])),
        ('OwnPage', '1'), ('children', [Orde[368 chars])])])`
        Which is useless.

        Args:
            d1: (any value) The obtained value from the tested method.
            d2: (any value) The expected value.
        """
        in_msg = ""
        if key is not None:
            in_msg = " in %s" % pformat(key)
        if not isinstance(d1, type(d2)):
            raise AssertionError("%s type for %s != type %s for %s%s"
                                 % (type(d1).__name__, d1,
                                    type(d2).__name__, d2, in_msg))
        if isinstance(d1, (OrderedDict, dict)):
            if d1.keys() != d2.keys():
                raise AssertionError("Keys %s != expected keys %s%s"
                                     % (d1.keys(), d2.keys(), in_msg))
            for key, value in d1.items():
                self.assertMoreEqual(value, d2[key], in_msg)
        elif isinstance(d1, list):
            if len(d1) != len(d2):
                raise AssertionError(
                    "len %s for %s != len %s for %s%s"
                    % (len(d1), d1, len(d2), d2, in_msg)
                )
            for i, value in enumerate(d1):
                self.assertMoreEqual(d1[i], d2[i], i)
                # if value != d2[i]:
                #     raise AssertionError("[%s]=%s != %s%s"
                #                         % (i, value, d2[i], in_msg))
        else:
            if d1 != d2:
                raise AssertionError("%s != %s%s"
                                     % (d1, d2, in_msg))

    def test_to_dict(self, data=None, strip=False):
        echo0("strip={}".format(strip))
        if data is None:
            data = xml_data
        root = from_string_scribus(data, skip_blank=strip)
        # import json
        # echo0(json.dumps(root.to_dict(enable_locations=False), indent=2))
        self.assertMoreEqual(
            root.to_dict(enable_locations=False),
            xml_data_dict,
            key="root",
        )

    def test_to_dict_with_spacing(self):
        self.test_to_dict(data=spaced_xml_data, strip=True)


if __name__ == "__main__":
    testcase = TestMoreScribus()
    count = 0
    for name in dir(testcase):
        if name.startswith("test"):
            echo0()
            echo0("Test {}...".format(name))
            fn = getattr(testcase, name)
            fn()  # Look at def test_* for the code if tracebacks start here
            count += 1
    echo0("%s test(s) passed." % count)
