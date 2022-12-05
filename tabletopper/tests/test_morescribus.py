# -*- coding: utf-8 -*-
"""
Created on Sun Dec 4, 2022

@author: Jake "Poikilos" Gustafson
"""


test_sgml_data='''        <PAGEOBJECT XPOS="766.0008" YPOS="30026.5978352942" OwnPage="72" ItemID="1378889691" PTYPE="2" WIDTH="522" HEIGHT="519.482352941148" FRTYPE="0" CLIPEDIT="0" PWIDTH="1" PLINEART="1" LOCALSCX="0.24" LOCALSCY="0.24" LOCALX="0" LOCALY="0" LOCALROT="0" PICART="1" SCALETYPE="1" RATIO="1" Pagenumber="0" PFILE="images/the_pyramid_and_mercury_mines_entrances.png" IRENDER="0" EMBEDDED="0" path="M0 0 L522 0 L522 519.482 L0 519.482 L0 0 Z" copath="M0 0 L522 0 L522 519.482 L0 519.482 L0 0 Z" gXpos="766.0008" gYpos="30026.5978352942" gWidth="0" gHeight="0" LAYER="0" NEXTITEM="-1" BACKITEM="-1"/>
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


import unittest
import sys
import os

my_dir = os.path.dirname(os.path.abspath(__file__))
module_dir = os.path.dirname(my_dir)
repo_dir = os.path.dirname(module_dir)

if __name__ == "__main__":
    sys.path.insert(0, repo_dir)

from tabletopper.morescribus import (
    SGML,
)

def echo0(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


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
        sgml = SGML(test_sgml_data)
        pfile_found = False
        for chunkdef in sgml:
            chunk = sgml.chunk_from_chunkdef(chunkdef)
            if chunkdef.get('tag') is None:
                continue
            if chunkdef.get('properties') is None:
                # It is a closing tag.
                continue
            pfile = chunkdef['properties'].get('PFILE')
            if pfile is not None:
                pfile_found = True
                self.assertEqual(
                    pfile,
                    "images/the_pyramid_and_mercury_mines_entrances.png",
                )
        self.assertTrue(pfile_found)


if __name__ == "__main__":
    testcase = TestMoreScribus()
    for name in dir(testcase):
        if name.startswith("test"):
            echo0()
            echo0("Test {}...".format(name))
            fn = getattr(testcase, name)
            fn()  # Look at def test_* for the code if tracebacks start here
