# -*- coding: utf-8 -*-
'''
This submodule is part of the booktacular module originally from
<https://github.com/Hierosoft/booktacular>.

Author: Jake "Poikilos" Gustafson

Process SLA files in a similar way as Python's HTMLParser so that you
can safely manipulate the files regardless of version. There is no
value checking, so it is mostly so that client code (such as
pull_images.py or your code that imports this submodule) can do
analysis and mass replacement.

The page numbering does *not* account for overflow frames, so all text
in the overflow will be considered part of the first box on the previous
page.

This submodule was started because:
- pyscribus fails to load "The Path of Resistance.sla" made in scribus
  (beta) 1.5.8 due to sanity checks and sanity checks are not desired
  since that makes the pyscribus module version-dependent and
  completely unusable due to version issues.
- SGMLParser is deprecated in (removed entirely from) Python 3
- lxml depends on libxml2 and libxslt which may not be
  easily/automatically installed on Windows (and may be too strict for
  SLA files)
  - Regardless, scribus is not valid XML. See
    <https://wiki.scribus.net/canvas/Scribus_files_as_XML> which
    has an XSLT file (.xsl xml definition file) and states that it
    requires a modified SLA file.

Possible alternatives:
- Run a Python script as an argument to scribus:
  `scribus -py some_script.py --python-arg v`
  -<https://stackoverflow.com/a/33370042/4541104>
'''
from __future__ import print_function
from __future__ import division
import sys
import os
# import re
import shutil
# import json
import copy

from collections import OrderedDict
from datetime import datetime
from pprint import pformat

if __name__ == "__main__":
    sys.path.insert(
        0,
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    )

from booktacular.find_hierosoft import hierosoft  # noqa: F401
# ^ works for submodules too since changes sys.path

from hierosoft import (  # noqa: F401
    echo0,
    echo1,
    echo2,
    echo3,
    echo4,
    write0,
    write1,
    write2,
    set_verbosity,
    get_verbosity,
)

from booktacular.find_pycodetool import pycodetool  # noqa: F401
# ^ works for submodules too since changes sys.path

from pycodetool.parsing import (
    explode_unquoted,
    find_whitespace,
    find_unquoted_even_commented,
)

# ASCII_BULLET = "0x2022"
UTF8_BULLET = b"\xE2\x80\xA2"  # hex editor
#   confirms this to be the 3 bytes where Scribus
#   inserted a bullet (The only bytes between the
#   single-byte quotes of CH="").

if hasattr(sys, 'maxint'):
    MAXINT = sys.maxint
    MININT = -sys.maxint  # There is no minint
else:
    # maxint is deprecated...there is no max!
    MAXINT = sys.maxsize
    MININT = -sys.maxsize


class SGMLLexer(object):
    '''Generate start, content, and end blocks.

    This is a generator that provides chunkdefs where each chunk is one
    of the CONTENT_ types. No context such as tag ancestors is
    calculated within this class. For the tree, see global parse
    function, which returns SGMLElementTree.

    When modifying a value of 'attributes', ensure that any double quote
    ('"') inside of is converted to "&quot;".

    Attributes:
        _data (string): The data (set via the feed method)
        skip_blank (bool): Causes the lexer (iteration or public
            "next" method) to completely omit whitespace-only content
            blocks (context==SGMLLexer.CONTENT).

    Returns:
        dict: chunkdef dictionary where start and end define a slice of
            the data, and 'context' is the CONTEXT_ constant which
            defines what type of data is at the slice. The slice can be
            obtained by passing the returned slice to the
            chunk_from_chunkdef() method.
    '''
    # formerly SGML

    START = "start"  # the return is a start tag such as <p>
    END = "end"  # the return is an end tag such as </p>
    CONTENT = "content"  # the return is content between tags

    def __init__(self, data, strict=True, skip_blank=None):
        if skip_blank is None:
            skip_blank = False
        elif skip_blank not in [True, False]:
            raise ValueError("skip_blank=%s (expected True or False)"
                             % pformat(skip_blank))
        self.skip_blank = skip_blank
        self._data = data
        self._chunkdef = None
        self.stack = []
        self.strict = strict

    def chunk_from_chunkdef(self, chunkdef, raw=False):
        '''Get a slice from a chunkdef.

        Args:
            chunkdef (dict): chunk definition that is returned by next
            raw (bool) If True, get the slice from the original data.
                This would happen even if False if not SGMLLexer.START.
                The raw option allows getting the underlying data that
                existed before 'attributes' was modified.

        Returns:
            string: The literal SGMLLexer chunk that represents the chunkdef.
                If 'context' is START, the tag will be generated from
                'attributes'! Otherwise, the result is a slice of
                self._data.
        '''
        # TODO: Replace this with node_from_chunkdef (return SGMLNode
        # or specific node type if well-known)
        if (chunkdef['context'] != SGMLLexer.START) or raw:
            if (not raw) and chunkdef.get('attributes') is not None:
                raise ValueError(
                    'A {} tag should not have attributes.'
                    ''.format(chunkdef['context'])
                )
            return self._data[chunkdef['start']:chunkdef['end']]
        chunk = "<" + chunkdef['tagName']
        # OrderedDict or Python (2.7+? or) 3.7+ must be used to maintain
        # the order:
        for key, value in chunkdef['attributes'].items():
            chunk += " "
            if not key.strip():
                raise ValueError(
                    "A property name must not be blank but got {}"
                    " (={})"
                    "".format(key, value)
                )
            for bad_chr in ["=", " "]:
                if bad_chr in key:
                    raise ValueError(
                        "A property name must not contain '{}' but got `{}`"
                        "".format(bad_chr, "{}={}".format(key, value))
                    )
            if value is None:
                chunk += key
            else:
                bad_chr = '"'
                if bad_chr in value:
                    raise ValueError(
                        'A property value must not contain "{}": {}="{}"'
                        ''.format(bad_chr, key, value)
                    )
                chunk += '{}="{}"'.format(key, value)
        if chunkdef.get('self_closer') is not None:
            chunk += chunkdef['self_closer'] + ">"
        else:
            chunk += ">"
        return chunk

    def feed(self, data):
        self._data += data

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self, cb_progress=None, event_template=None):
        """Lex (not parse) the next chunk, which can be start, content, or end

        For context and making a tree, see the "parse" method.

        Args:
            cb_progress (function): Callback that accepts a
                dict where 'ratio' is a float from 0.0 to 1.0
                (inaccurate if using "feed" method).
        """
        prefix = "[SGMLLexer next] "
        if cb_progress is None:
            def cb_progress(evt):
                sys.stderr.write(
                    "\r" + prefix + "{}%".format(round(evt['ratio'] * 100, 1))
                )
        previous = self._chunkdef
        self._chunkdef = {}
        if event_template is None:
            evt = {}
        else:
            evt = copy.deepcopy(event_template)

        if previous is None:
            start = 0
        else:
            start = previous['end']
            if start == previous['start']:
                # Prevent an infinite loop.
                raise RuntimeError(
                    "The index didn't move from {}".format(start)
                )
        if start > len(self._data):
            raise RuntimeError(
                "start is {} which is past len(self._data)={}"
                "".format(start, len(self._data))
            )
        if start == len(self._data):
            evt['ratio'] = 1.0
            cb_progress(evt)
            raise StopIteration()
        evt['ratio'] = float(start) / float(len(self._data))
        cb_progress(evt)
        # ^ may be inaccurate if using "feed" method
        self._chunkdef['start'] = start
        if self._data[start:start + 2] == "</":
            self._chunkdef['context'] = SGMLLexer.END
        elif self._data[start] == "<":
            self._chunkdef['context'] = SGMLLexer.START
        elif self._data[start:start + 1] == ">":
            echo0('Warning: unexpected > at character number {}'
                  ''.format(start))
            self._chunkdef['context'] = SGMLLexer.CONTENT
        else:
            self._chunkdef['context'] = SGMLLexer.CONTENT

        if self._chunkdef['context'] == SGMLLexer.CONTENT:
            self._chunkdef['end'] = self._data.find("<", start + 1)
            if self._chunkdef['end'] < 0:
                self._chunkdef['end'] = len(self._data)
                content = self._data[self._chunkdef['start']:]
                if content.strip() or self.stack:
                    message = (
                        'Warning: The file ended before a closing tag'
                        ' for {} after extra content: "{}".'
                        ''.format(
                            self._stack_tagNames(),
                            content,
                        )
                    )
                    if len(self.stack) > 0:
                        message += (" (while still in content in {})"
                                    "".format(content))
                    else:
                        message += " (after all tags were closed)"
                    echo0(message)
                    del message
        else:
            self._chunkdef['end'] = find_unquoted_even_commented(
                self._data,
                ">",
                start + 1,
                quote_marks='"',
            )
            if self._chunkdef['end'] < start + 1:
                raise RuntimeError(
                    "The '<' at {} wasn't closed."
                    "".format(start)
                )
            self._chunkdef['end'] += 1  # The ender is exclusive: include ">".
            chunk = self.chunk_from_chunkdef(self._chunkdef, raw=True)
            # echo0("{} chunk={}"
            #       "".format(self._chunkdef['context'], chunk))
            # ^ includes the enclosing signs
            if self._chunkdef['context'] == SGMLLexer.START:
                props_end = len(chunk) - 1  # exclude '>'.
                if chunk.endswith("/>"):
                    props_end -= 1
                    self._chunkdef['self_closer'] = "/"
                elif chunk.endswith("?>"):
                    props_end -= 1
                    self._chunkdef['self_closer'] = "?"
                    # Such as `<?xml version="1.0" encoding="UTF-8"?>`

                # self._chunkdef['attributes'] = OrderedDict()
                # As of Python 3.7, dict order is guaranteed to be the
                #   insertion order, but OrderedDict
                #   is still required to support reverse (and
                #   OrderedDict's own move_to_end method).
                #   -<https://stackoverflow.com/a/50872567/4541104>
                self._chunkdef['attributes'] = OrderedDict()
                attributes = self._chunkdef['attributes']
                # prop_abs_start = self._chunkdef['start']
                props_start = find_whitespace(chunk, 0)
                if props_start > -1:
                    self._chunkdef['tagName'] = chunk[1:props_start].strip()
                    # ^ 1 to avoid "<" and props_start to end before the
                    #   first whitespace.
                    statements = explode_unquoted(
                        chunk[props_start:props_end],
                        " ",
                        quote_marks='"',
                        allow_commented=True,
                        allow_escaping_quotes=False,
                    )
                    for statement_raw in statements:
                        statement = statement_raw.strip()
                        if len(statement) == 0:
                            continue
                        sign_i = statement.find("=")
                        if sign_i > -1:
                            key = statement[:sign_i].strip()
                            value = statement[sign_i + 1:].strip()
                            if ((len(value) >= 2) and (value[0] == '"')
                                    and (value[-1] == '"')):
                                value = value[1:-1]
                            attributes[key] = value
                        else:
                            # It is a value-less property.
                            key = statement
                            attributes[key] = None
                else:
                    echo4("There are no attributes in `{}`"
                          "".format(chunk[:30] + "..."))
                    # There are no attributes.
                    self._chunkdef['tagName'] = chunk[1:props_end].strip()
                    # ^ 1 to avoid "<" and -1 to avoid ">"
                if self._chunkdef.get('self_closer') is None:
                    self.stack.append(self._chunkdef)
            elif self._chunkdef['context'] == SGMLLexer.END:
                self._chunkdef['tagName'] = chunk[2:-1].strip()
                # ^ 2 to avoid both "<" and "/" since an SGMLLexer.END.
                if len(self.stack) < 1:
                    if self.strict:
                        raise SyntaxError(
                            "{} ended at {} before a matching opening tag"
                            " (expected {})"
                            "".format(
                                self._chunkdef['tagName'],
                                start,
                                self._stack_tagNames(),
                            )
                        )
                elif self._chunkdef['tagName'] != self.stack[-1]['tagName']:
                    if self.strict:
                        raise SyntaxError(
                            "{} ended at {} before the expected {}"
                            "".format(
                                self._chunkdef['tagName'],
                                start,
                                self._stack_tagNames(),
                            )
                        )
                else:
                    del self.stack[-1]
            # end else not SGMLLexer.CONTENT
        if self._chunkdef['context'] == SGMLLexer.CONTENT:
            value = self._data[self._chunkdef['start']:self._chunkdef['end']]
            if not value.strip():
                if self.skip_blank:
                    # Do not return this blank one. Instead, recurse.
                    return self.next(
                        cb_progress=cb_progress,
                        event_template=event_template,
                    )
            # else:
            #     if self.skip_blank:
            #         raise NotImplementedError(
            #             "Non-blank content in Scribus file")
        return self._chunkdef

    def _stack_tagNames(self):
        """Get a list of the current tagNames that are still open.

        Returns:
            list: tagName strings from innermost to outermost.
        """
        results = []
        for i in reversed(range(0, len(self.stack))):
            results.append(self.stack[i]['tagName'])
        return results


class ScribusPage(object):
    """Manage elements on a single Scribus page.

    Attributes:
        number (int): The page number (may be -1)
    """
    # not SGMLPage because this is specific to Scribus

    def __init__(self):
        self.children = []
        self.node = None
        self.root = None
        self.document = None
        self.number = None

    def add_child(self, node):
        known_objects = [
            "PAGEOBJECT",
            "MASTEROBJECT",
            "PatternItem",
            "FRAMEOBJECT",
        ]
        if node.tagName == "PAGEOBJECT":
            # May include "StoryText" tag under it
            #   unless self_closer is set, then it
            #   is probably a picture ('PFILE' attribute)
            new_node = ScribusPageObject()
            new_node.update(node)
        elif node.tagName == "MASTEROBJECT":
            # Such as page number
            new_node = ScribusPageObject()
            new_node.update(node)
        elif node.tagName == "PatternItem":
            new_node = ScribusPatternItem()
            new_node.update(node)
            # raise NotImplementedError(
            #     'Pattern has OwnPage="-1" but PatternItem'
            #     ' has a parent. Add Pattern instead.'
            # )
        elif node.tagName == "FRAMEOBJECT":
            new_node = ScribusFrameObject()
            new_node.update(node)
        else:
            raise NotImplementedError(
                "got %s expected one of: %s"
                % (node.tagName, known_objects)
            )
        if node.ancestor_has_attribute("OwnPage"):
            raise NotImplementedError("Nested OwnPage")
        self.children.append(new_node)

    def get_width(self):
        """Get width in points (1/72 in)
        """
        return int(self.document.attributes['PAGEWIDTH'])

    def get_height(self):
        """Get height in points (1/72 in)
        """
        return int(self.document.attributes['PAGEHEIGHT'])

    def safe_width(self):
        """Get width minus margins in points (1/72 in).
        """
        return int(
            self.get_width()
            - int(self.document.attributes['BORDERLEFT'])
            - int(self.document.attributes['BORDERRIGHT'])
        )

    def safe_height(self):
        """Get height minus margins in points (1/72 in).
        """
        return int(
            self.get_height()
            - int(self.document.attributes['BORDERTOP'])
            - int(self.document.attributes['BORDERBOTTOM'])
        )

    def wide_and_narrow_children(self):
        """Separate wide and narrow page objects.

        Returns:
            tuple[list[ScribusPageObject]]: wide_children, narrow_children
        """
        half_w = self.safe_width() // 2
        big_w = half_w + half_w // 6
        # ^ increase threshold slightly since a picture with a blank
        #   background may be a little bigger than half the page.
        wide = []
        narrow = []
        for child in self.children:
            if child.get_float("WIDTH") > big_w:
                wide.append(child)
            else:
                narrow.append(child)
        return (wide, narrow)

    def left_and_right_children(self, narrow_children):
        """Separate left and right column objects by center_x of each.

        Only use this for narrow_children, otherwise assume that there is
        only one column.

        Args:
            narrow_children (list[ScribusPageObject]): The 2nd element
                of the self.wide_and_narrow_children() tuple which only
                has children that are the size of a column.
        """
        half_w = self.safe_width() // 2
        center_x = int(self.document.attributes['BORDERLEFT']) + half_w
        left = []
        right = []
        for child in narrow_children:
            if child.center_x < center_x:
                left.append(child)
            else:
                right.append(child)
        return left, right

    def sort_children_spatially(self):
        """Sort children by column.

        Left then right sorting is normal but can be overridden by an
        object that is 2 columns wide as determined by
        wide_and_narrow_children.
        """
        if self.document is None:
            raise ValueError("DOCUMENT node is not set.")
        prefix = "[sort_children_spatially] "
        echo0(prefix + "sorting page %s+1=%s" % (self.number, self.number + 1))
        new_children = []
        wide_children, narrow_children = self.wide_and_narrow_children()

        wide_children = sorted(wide_children)
        narrow_children = sorted(narrow_children)
        # ^ sorted requires the ScribusPageObject subclass which implements
        #   dunder methods used by sorting.
        tmp = ScribusPageObject()
        tmp.attributes = OrderedDict()
        tmp.attributes['YPOS'] = None
        TMP_TAGNAME = "morescribus tmp"
        tmp.tagName = TMP_TAGNAME
        tmp.attributes['HEIGHT'] = 72 // 4  # 72 is 1 inch.
        min_y = None
        # last tier has to be above all children:
        for child in narrow_children:
            if tmp.ypos is None or child.ypos > tmp.ypos:
                tmp.attributes["YPOS"] = child.ypos
            if min_y is None or child.ypos < min_y:
                min_y = child.ypos
        # first minimum needs to be below all tiers too
        #   (for bounds checking--see RuntimeError further down):
        for child in wide_children:
            if min_y is None or child.ypos < min_y:
                min_y = child.ypos

        if len(narrow_children) > 0:
            tmp.attributes["YPOS"] += 1
        else:
            # echo0("Warning, no single-column elements in page %s+1=%s"
            #       % (self.number, self.number+1))
            # ^ This warning is commented since the recommended way to do
            #   2 columns in scribus is *1* box with columns set to 2.
            if hasattr(sys, 'maxint'):
                tmp.attributes['YPOS'] = MAXINT
            else:
                # maxint is deprecated...there is no max!
                tmp.attributes['YPOS'] = MAXINT
        if min_y is None:
            min_y = MININT
        if len(wide_children) == 0:
            echo0("There are no wide elements in page %s+1=%s"
                  % (self.number, self.number + 1))
        if len(wide_children) + len(narrow_children) != len(self.children):
            echo0("%s wide and %s narrow do not add up to %s total"
                  " on page %s+1=%s"
                  % (len(wide_children), len(narrow_children),
                     len(self.children), self.number, self.number + 1))
        wide_children.append(tmp)  # to reorder left or right less than each
        for child in narrow_children:
            child.done = False
        left_children, right_children = \
            self.left_and_right_children(narrow_children)
        # echo0(prefix+"Sorting page %s" % (self.number + 1))
        for divider in wide_children:
            # echo0(prefix+"writing %s <= y < %s" % (min_y, divider.ypos))
            for child in left_children:
                if child.ypos < divider.ypos and child.ypos >= min_y:
                    new_children.append(child)
            for child in right_children:
                if child.ypos < divider.ypos and child.ypos >= min_y:
                    new_children.append(child)
            if divider.tagName == TMP_TAGNAME:
                continue
            new_children.append(divider)
            if divider.ypos < min_y:
                points = []
                for _divider in wide_children:
                    points.append((_divider.xpos, _divider.ypos))
                raise RuntimeError("Sorting failed. ypos %s < %s in: %s"
                                   % (divider.ypos, min_y, points))
            min_y = divider.ypos
        if len(self.children) != len(new_children):
            raise NotImplementedError("Not all children were sorted.")
        self.children = new_children

    def dump_text(self, stream):
        """Write only visible text of children to stream.

        Call sort_children_spatially *before* this for spatial sorting.
        """
        for sub in self.children:
            # _dump_text_unsorted since children of PAGEOBJECT
            #   (but not PAGEOBJECTs themselves) are in order of appearance(?)
            sub._dump_text_unsorted(
                stream,
                sub.parent,
                self.root,
                sub,
                sub,
                attribute="CH",
                image_attribute="PFILE",
                paragraph_tags=["PAGEOBJECT", "para"],
                tab_tags=["tab"],
                tab_mark="\t"
            )


class SGMLText(object):
    """The most simple chunk in XML/SGML is text (in/after tags).

    Attributes:
        value (string): text
        parent (SGMLNode): Node that contains text
        start (int): position in file
        end (int): end position in file (exclusive)
    """
    KEYS = ['start', 'end', 'value', 'context']

    def __init__(self):
        object.__init__(self)
        self.value = None
        self.parent = None
        self.start = None
        self.end = None

    def startswith(self, value, attribute=None, encoding=None,
                   test_fail=False):
        """Check if starts with a value.
        Args:
            encoding (Optional[string]): An encoding string recognized
                by Python str's "encode" method. Defaults to "utf-8".
            test_fail (Optional[bool]): If True, a non-match
                raises an exception.
        """
        if not encoding:
            encoding = "utf-8"
        if test_fail is None:
            test_fail = False
        self_value_bytes = self.value
        if attribute:
            if not hasattr(self, 'attributes'):
                if test_fail and value == UTF8_BULLET:
                    raise NotImplementedError("uh oh")
                return False
            attr_value = self.attributes.get(attribute)
            if not attr_value:
                if test_fail and value == UTF8_BULLET:
                    raise NotImplementedError("uh oh")
                return False
            self_value_bytes = attr_value
        if not self_value_bytes:
            if test_fail and value == UTF8_BULLET:
                raise NotImplementedError("uh oh")
            return False

        if not isinstance(self_value_bytes, type(value)):
            if isinstance(value, (bytes, bytearray)):
                if isinstance(self_value_bytes, str):
                    self_value_bytes = type(value)(
                        self_value_bytes.encode(encoding)
                    )
                elif isinstance(self_value_bytes, (bytes, bytearray)):
                    self_value_bytes = type(value)(self_value_bytes)
                else:
                    raise TypeError(
                        "Conversion from %s"
                        " to %s is not implemented."
                        % (type(self.value).__name__, type(value).__name__)
                    )
            elif isinstance(value, str):
                if isinstance(value, (bytes, bytearray)):
                    self_value_bytes = \
                        bytes(self_value_bytes).decode(encoding)
            else:
                raise TypeError(
                    "Conversion from %s"
                    " to %s is not implemented."
                    % (type(self.value).__name__, type(value).__name__)
                )
        if test_fail and not self_value_bytes.startswith(value):
            if value == UTF8_BULLET:
                raise NotImplementedError(
                    "uh oh %s(%s) != %s(%s)"
                    % (type(self_value_bytes).__name__,
                       pformat(self_value_bytes),
                       type(value).__name__, pformat(value))
                )

        return self_value_bytes.startswith(value)

    def is_root(self):
        """Should only be True class that only has children not tag.

        See redefinition in subclass such as SGMLElementTree.
        """
        return False

    @property
    def context(self):
        return SGMLLexer.CONTENT

    def get_value(self, attribute=None):
        value = None
        if attribute:
            if hasattr(self, 'attributes'):
                value = self.attributes.get(attribute)
            # else there is nothing to get.
        elif hasattr(self, 'value'):
            value = self.value
        return value

    def get_float(self, attribute_name):
        """Get attribute as float.

        This should handle attributes of all subclasses.
        """
        if not hasattr(self, 'attributes') or not self.attributes:
            return None
        value = self.attributes.get(attribute_name)
        if value is None:
            return None
        return float(value)

    def get_int(self, attribute_name):
        """Get attribute as int.

        This should handle attributes of all subclasses.
        """
        if not hasattr(self, 'attributes') or not self.attributes:
            return None
        value = self.attributes.get(attribute_name)
        if value is None:
            return None
        return int(value)

    def get(self, attribute_name):
        """Get attribute without any type conversion.

        This should handle attributes of all subclasses.
        """
        if not hasattr(self, 'attributes') or not self.attributes:
            return None
        return self.attributes.get(attribute_name)

    def _self_or_ancestor_has_attribute(self, attribute_key):
        if hasattr(self, 'attributes'):
            if 'attribute_key' in self.attributes:
                return True
        if self.parent is not None:
            return self.parent._self_or_ancestor_has_attribute(
                attribute_key,
            )

    def ancestor_has_attribute(self, attribute_key):
        if self.parent is not None:
            return self.parent._self_or_ancestor_has_attribute(
                attribute_key,
            )
        return False

    def to_dict(self, enable_locations=True):
        result = OrderedDict()
        for key in type(self).KEYS:
            if key == "self_closer":
                if self.self_closer is not None:
                    result[key] = self.self_closer
            elif (key in ("start", "end")) and not enable_locations:
                pass
            elif key == "context":
                if self.is_root():
                    # Root only has children, not a tag.
                    # result[key] = SGMLLexer.START
                    pass
                elif self.context is not None:
                    result[key] = self.context
                else:
                    # Should never get this error on
                    #   SGMLElementTree since is_root() is True
                    raise NotImplementedError(
                        "type %s" % type(self).__name__
                    )
            else:
                result[key] = getattr(self, key)
        if hasattr(self, 'children') and len(self.children) > 0:
            result['children'] = []
            for child in self.children:
                result['children'].append(
                    child.to_dict(
                        enable_locations=enable_locations,
                    )
                )
        return result

    @staticmethod
    def from_chunkdef(chunkdef):
        result = SGMLText()
        result._from_chunkdef(chunkdef)
        return result

    def _from_chunkdef(self, chunkdef):
        for key, value in chunkdef.items():
            if key in type(self).KEYS:
                if key == 'context':
                    if value != SGMLLexer.CONTENT:
                        raise NotImplementedError(
                            "Only %s context can be converted to SGMLText"
                        )
                else:
                    setattr(self, key, value)
            else:
                raise NotImplementedError(
                    "%s can only have %s (insure KEYS matches SGMLLexer code)"
                    % (type(self).__name__, type(self).KEYS)
                )

    def _collect_pages(self, parent, root, pos_node, page_node, document_node):
        attributes = None
        XPOS = None
        YPOS = None
        CH = None
        OwnPage = None

        if hasattr(self, 'attributes'):
            attributes = self.attributes
            CH = attributes.get('CH')
            XPOS = attributes.get('XPOS')
            YPOS = attributes.get('YPOS')
            if attributes.get("OwnPage") is not None:
                page_node = self
                OwnPage = int(attributes['OwnPage'])
                if OwnPage not in root._pages:
                    root._pages[OwnPage] = ScribusPage()
                    root._pages[OwnPage].node = self
                    root._pages[OwnPage].root = root
                    root._pages[OwnPage].document = document_node
                    root._pages[OwnPage].number = int(OwnPage)
                root._pages[OwnPage].add_child(self)

            if XPOS is not None:
                if YPOS is not None:
                    pos_node = self
                else:
                    raise NotImplementedError("XPOS without YPOS at %s"
                                              % self.start)
        if XPOS is None or YPOS is None:
            if pos_node:
                XPOS = pos_node.attributes['XPOS']
                YPOS = pos_node.attributes['YPOS']
        if OwnPage is None:
            if page_node:
                OwnPage = page_node.attributes['OwnPage']

        tagName = None
        tagNameUpper = None
        if hasattr(self, 'tagName'):
            tagName = self.tagName
            if tagName is not None:
                tagNameUpper = tagName.upper()
                if tagNameUpper == "DOCUMENT":
                    document_node = self
        children = None
        if hasattr(self, 'children'):
            children = self.children
        if children:
            for child in children:
                child._collect_pages(self, root, pos_node, page_node,
                                     document_node)

    def _dump_text_unsorted(self, stream, parent, root, pos_node, page_node,
                            attribute=None, image_attribute=None, indent=None,
                            paragraph_tags=None, para_mark=None, tab_tags=None,
                            tab_mark=None):
        # if node['tagName'].upper() == "PAGEOBJECT":

        # if tagName.lower() != 'ITEXT':
        #     # CH attribute (displayable text) is usually in ITEXT.
        #     return
        if para_mark is None:
            para_mark = "\n\n"
        attributes = None
        children = None
        if indent is None:
            indent = ""
        if hasattr(self, 'tagName'):
            # echo0(indent+"processing %s" % self.tagName)
            if paragraph_tags:
                if self.tagName in paragraph_tags:
                    stream.write(para_mark)
            if tab_tags:
                if self.tagName in tab_tags:
                    stream.write(tab_mark)
        else:
            pass
            # echo0(indent+"processing")
        if hasattr(self, 'attributes'):
            attributes = self.attributes
        value = self.get_value(attribute=attribute)
        image = None
        if image_attribute:
            image = self.get_value(attribute=image_attribute)
        if attribute:
            if not value:
                if hasattr(self, 'tagName'):
                    if self.tagName == "ITEXT":
                        raise ValueError("No %s though tagName is %s"
                                         " for %s"
                                         % (attribute, self.tagName,
                                            self.to_dict(),))
                if not image:
                    pass
                    # This is ok, it may be PAGEOBJECT containing
                    #   StoryText containing DefaultStyle, ITEST, trail, etc.
                    # raise ValueError("No %s (nor image_attribute=%s)"
                    #                  " in %s"
                    #                 % (attribute, image_attribute,
                    #                    self.to_dict(),))
        if hasattr(self, 'children'):
            children = self.children
        if image is not None:
            alt = ""
            # TODO: Support HTML? Something like:
            # if value is not None:
            #     alt = value
            # else:
            date_str = ""
            if os.path.isfile(image):
                file_ts = os.path.getmtime(image)
                dt = datetime.fromtimestamp(file_ts)
                date_str = ": " + dt.strftime("%Y-%d-%m %H:%M:%S")
            else:
                raise FileNotFoundError("No such file: %s" % image)
            image_no_ext, _ = os.path.splitext(os.path.basename(image))
            image_name = image_no_ext.replace("_", " ").replace("-", " ")
            alt = "%s%s" % (image_name, date_str)
            stream.write("\n![%s](%s)\n" % (alt, image))
        elif value is not None:
            markdown = value.replace(UTF8_BULLET.decode("utf-8"), "*")
            try:
                _ = int(value)
                raise ValueError(
                    "expected data, got number: %s"
                    % self.to_dict()
                )
            except ValueError:
                pass  # this is good
            stream.write(markdown)  # Often there is no newline
            #   even in a new ITEXT element such as after a bullet
            #   in scribus format.
        if children is None:
            if attribute and not value and not image:
                # Probably SGMLText with nothing in it.
                #   whitespace may not be correct, because this
                #   triggers. However, Scribus doesn't use
                #   content.
                # TODO: Make a test for getting values (between tags)
                # raise ValueError("No %s (nor image_attribute=%s)"
                #                     " and no children in %s"
                #                 % (attribute, image_attribute,
                #                     self.to_dict(),))
                pass
            return

        for i, child in enumerate(children):
            prev_child = children[i - 1] if i > 0 else None
            # ^ The prev child may not be a bullet such as in
            #   Scribus format:
            #   <para PARENT
            #   <ITEXT FONT  ... [where CH is only a bullet character]
            #   <ITEXT FONTSIZE ... [where CH is text after bullet]
            next_child = children[i + 1] if (i + 1 < len(children)) else None
            if next_child:
                # In The Path of Resistance.sla, if the
                # previous child contains "and giant sil" then the
                # current child should be para and the
                # next child should start with bullet:
                if next_child.startswith(UTF8_BULLET, attribute=attribute):
                    para_mark = "\n"  # only 1 newline, para between bullets
                else:  # There is no bullet next
                    # There is known to be another bullet after
                    #   after_prev_bullet prior to this child (para). If
                    #   that bullet isn't next, parsing failed (or
                    #   UTF8_BULLET is not decoded correctly).
                    after_prev_bullet = "giant silhouettes"  # prev_child
                    prev_child_value = None
                    if prev_child:
                        prev_child_value = \
                            prev_child.get_value(attribute=attribute)
                    # child_value = child.get_value(attribute)
                    # ^ unused (*always blank* for para in Scribus format)
                    if (prev_child_value
                            and (after_prev_bullet in prev_child_value)):
                        _ = next_child.startswith(UTF8_BULLET,
                                                  attribute=attribute,
                                                  test_fail=True)

                        # since this is the ELSE case for below, above
                        #   should be False (Match should have para
                        #   [this child] then bullet[next child])
                        raise ValueError(
                            "No bullet in value=%s in "
                            "\n  next_child %s"
                            "\n  (this=%s)"
                            "\n  (previous=%s)"
                            % (
                                pformat(
                                    next_child.get_value(attribute=attribute)
                                ),
                                next_child.to_dict(),
                                child.to_dict(),
                                prev_child.to_dict(),
                            )
                        )
            child._dump_text_unsorted(
                stream,
                self,
                root,
                pos_node,
                page_node,
                attribute=attribute,
                image_attribute=image_attribute,
                indent=indent + "  ",
                paragraph_tags=paragraph_tags,
                para_mark=para_mark,
                tab_tags=tab_tags,
                tab_mark=tab_mark,
            )
        return


class SGMLNode(SGMLText):
    """
    context is *not* an attribute. It maps to a Python type
    (SGMLText or SGMLNode).

    Attributes:
        tagName (string): The tagName.
    """
    KEYS = ['start', 'end', 'context', 'tagName', 'attributes', 'self_closer']

    def __init__(self):
        SGMLText.__init__(self)
        self.tagName = None  # from 'tagName'
        self.attributes = OrderedDict()  # from 'attributes'
        self.self_closer = None
        self.children = []  # Determined by the `populate` method.

    @property
    def context(self):
        return SGMLLexer.START

    @staticmethod
    def from_chunkdef(chunkdef):
        result = SGMLNode()
        result._from_chunkdef(chunkdef)
        return result

    def _from_chunkdef(self, chunkdef):
        for key, value in chunkdef.items():
            if key in type(self).KEYS:
                if key == 'context':
                    if value != SGMLLexer.START:
                        raise NotImplementedError(
                            "Only %s context can be converted to SGMLText"
                            " but context=%s"
                            % (SGMLLexer.START, value)
                        )
                elif key == 'attributes':
                    self.attributes = OrderedDict()
                    for attr_key, attr_value in value.items():
                        self.attributes[attr_key] = attr_value
                elif key == 'value':
                    self.value = value
                    raise NotImplementedError(
                        "unexpected value in opening"
                        " (should be in next SGMLText)"
                    )
                else:
                    setattr(self, key, value)
            else:
                raise ValueError("%s should only have %s but has %s"
                                 % (type(self).__name__, SGMLText.KEYS, key))

    def cb_progress_populate(self, evt):
        ratio = evt.get('ratio')
        if ratio:
            sys.stderr.write("\rParsing...{}%".format(round(ratio * 100, 1)))
            sys.stderr.flush()

    def cb_done_populate(self, evt):
        echo0("...Done")  # finish the line that cb_progress_populate started.

    def _populate(self, lexer, cb_progress=None):
        """Parse chunks from lexer and create children recursively.

        This does *not* take cb_done because it is recursive. For the cb_done
        call, see populate (no underscore) instead.
        """
        try:
            while True:
                chunkdef = lexer.next(cb_progress=cb_progress)
                context = chunkdef['context']
                if context in (SGMLLexer.START, SGMLLexer.CONTENT):
                    if context == SGMLLexer.START:
                        child = SGMLNode.from_chunkdef(chunkdef)
                    else:
                        child = SGMLText.from_chunkdef(chunkdef)
                    child.parent = self
                    self.children.append(child)
                    if context == SGMLLexer.START:
                        if child.self_closer is None:
                            child._populate(
                                lexer,
                                cb_progress=cb_progress,
                            )
                        # else self-closing so next child also belongs to self
                elif context == SGMLLexer.END:
                    # return to parent
                    break
                else:
                    raise NotImplementedError("Unknown context: %s"
                                              % context)
        except StopIteration:
            pass

    def populate(self, lexer, cb_progress=None, cb_done=None):
        """

        cb_done should *not* be called from here, since it is recursive.
        Args:
            lexer (SGMLLexer): The SGMLLexer
            cb_progress (Callable): The progress callback must take
                a dict including 'ratio' from 0.0 to 1.0 for progress.
            cb_done (Callable): The done callback is notified when
                the entire recursive progress is done, unless the
                'error' key of the sent dict is not None.
        """
        if cb_progress is None:
            cb_progress = self.cb_progress_populate
        if cb_done is None:
            cb_done = self.cb_done_populate
        self._populate(
            lexer,
            cb_progress=cb_progress,
        )
        cb_done({})


class ScribusPageObject(SGMLNode):
    def __init__(self):
        SGMLNode.__init__(self)

    def update(self, node):
        """Become like a node.
        """
        # for key in type(node).KEYS:
        #     if key == "context":
        #         # This is the type after parsed
        #         #   (key is only in unparsed dict from lexer, not OO)
        #         pass
        #     else:
        #         setattr(self, key, getattr(node, key))
        # ^ KEYS are not really enough, because KEYS are
        #   only the members copied directly from the
        #   unparsed dictionary generated by the lexer.
        #   There are also members generated by the
        #   parser such as children.
        #   So get all values from vars (same as __dict__):
        for key, value in vars(node).items():
            setattr(self, key, value)

    @property
    def OwnPage(self):
        if not hasattr(self, 'attributes') or not self.attributes:
            return None
        return self.attributes.get('OwnPage')

    @property
    def xpos(self):
        """Get the XPOS attribute as a float in "points" units.

        Often they are whole numbers, but not always.
        """
        return self.get_float("XPOS")

    @property
    def ypos(self):
        return self.get_float("YPOS")

    def __lt__(self, other):
        """Override the dunder "less than" method since used by sorted.
        """
        if self.ypos == other.ypos:
            return self.xpos < other.xpos
        return self.ypos < other.ypos

    def __eq__(self, other):
        """Override the dunder "equals" method since used by sorted.
        """
        return self.ypos == other.ypos

    @property
    def width(self):
        return self.get_float("WIDTH")

    @property
    def height(self):
        return self.get_float("HEIGHT")

    @property
    def pfile(self):
        return self.get("PFILE")

    @property
    def bottom(self):
        return self.ypos + self.height

    @property
    def right(self):
        return self.xpos + self.width

    @property
    def center_x(self):
        return self.xpos + self.width // 2

    @property
    def center_y(self):
        return self.ypos + self.height // 2


class ScribusFrameObject(ScribusPageObject):
    def __init__(self):
        ScribusPageObject.__init__(self)

    # @property
    # def OwnPage(self):
    #     if len(self.children) != 1:
    #         raise NotImplementedError(
    #             "FRAMEOBJECT should have only StoryText but has %s"
    #             % len(self.children)
    #         )
    #     # StoryText = self.children[0]
    #     if not hasattr(self, 'attributes') or not self.attributes:
    #         return None
    #     return self.attributes.get('OwnPage')


class ScribusPatternItem(ScribusPageObject):
    def __init__(self):
        ScribusPageObject.__init__(self)

    @property
    def Pattern(self):
        # Not really important since ScribusPatternItem
        #   has ownPage. Pattern only has the larger width etc.
        return self.parent


class SGMLElementTree(SGMLNode):
    """A hierarchical structure of SGML nodes.

    Attributes:
        _lexer (SGMLLexer): Iterate through chunks in the raw data
            (not hierarchical nor OO until parse places results in children).
        children (list[Union(SGMLNode,SGMLText)]): In the case
            of SGMLElementTree, children includes one that is root.
    """
    def __init__(self):
        SGMLNode.__init__(self)
        self._lexer = None
        self._pages = None

    @property
    def context(self):
        return None

    def is_root(self):
        """Should only be True class that only has children not tag.
        """
        return True

    def dump_text_unsorted(self, stream, attribute=None,
                           image_attribute=None):
        '''Dump all text in order or XML not actual order.
        '''
        if self._lexer is None:
            raise RuntimeError("you must lex and parse first.")

        if self.children is None:
            raise RuntimeError("you must parse first.")

        for sub in self.children:
            sub._dump_text_unsorted(stream, self, self, None, None,
                                    attribute=attribute,
                                    image_attribute=image_attribute)

    def parse(self, lexer):
        self._lexer = lexer
        if lexer._data is None:
            raise ValueError(
                "The file was not lexed. See (or use) morescribus.parse"
                " or morescribus.from_string for correct usage of object"
            )
        echo0("Parsing...")
        min_page = None
        max_page = None
        self.populate(lexer)
        # self.children = self._parse(lexer, self, None, None, None)


class ScribusDocRoot(SGMLElementTree):
    def __init__(self):
        SGMLElementTree.__init__(self)

    def get_root(self):
        for sub in self.children:
            if not hasattr(sub, 'children'):
                continue
            # if sub.tagName == "SCRIBUSUTF8NEW":
            for sub_sub in sub.children:
                if not hasattr(sub_sub, 'tagName'):
                    continue
                if sub_sub.tagName == "DOCUMENT":
                    return sub_sub
        return None

    def get_title(self):
        real_root = self.get_root()
        return real_root.attributes['TITLE']

    def dump_text(self, stream):
        '''Dump all text in spatial order, respecting up to 2 columns.

        Also respect multiple sections per page (if there is a box the
        width of the whole page, the column order automatically changes
        - from: left, right
        - to: top-left, top-right, full-width-box, bottom-left, bottom-right
        '''
        prefix = "[dump_text] "
        if self._lexer is None:
            raise RuntimeError("you must lex and parse first.")

        if self.children is None:
            raise RuntimeError("you must parse first.")

        # if self._pages is None:
        self.collect_pages()
        first = None
        last = None
        for key in self._pages.keys():
            if not isinstance(key, int):
                raise KeyError("Expected int for page key, got %s(%s)"
                               % (type(key).__name__, pformat(key)))
            index = key
            if first is None or index < first:
                first = index
            if last is None or index > last:
                last = index

        if first is None:
            # collect_pages should add pages if there is *any*
            #   element with an OwnPage attribute. If not,
            #   There are no visible objects (or collect_pages is wrong).
            raise RuntimeError("There are no visible objects with OwnPage.")

        if first < 0:
            # Do not display invisible items. For example the following may
            #   appear twice in the document for some reason (after deleted?):
            #         <FRAMEOBJECT ... OwnPage="-1" ...>
            #             <StoryText>
            #                 <DefaultStyle/>
            #                 <ITEXT CH="Tali Red"/>
            #                 <para PARENT="Creature - name"/>
            #                 <ITEXT CH="Tali Red seems like ... />
            #                 <trail PARENT="Creature - summary"/>
            #             </StoryText>
            #         </FRAMEOBJECT>
            # There are several instances of this where there are
            #   multiple duplicates and then there is a FRAMEOBJECT
            #   with OwnPage that is >= 0.
            first = 0
        count = 0
        stream.write(
            "\n\n"
            "# %s\n"
            % (self.get_title())
        )
        for index in range(first, last + 1):
            page = self._pages.get(index)
            if page is None:
                echo1("Blank page %s+1=%s (not in %s)"
                      % (pformat(index), index + 1,
                         list(sorted(self._pages.keys()))))
                # There is no PAGEOBJECT/other visible on this page.
                continue
            count += 1
            prev_len = len(self.children)
            page.sort_children_spatially()
            if len(self.children) != prev_len:
                raise NotImplementedError(
                    "element count was reduced from %s to %s"
                    % (prev_len, len(self.children))
                )
            stream.write(
                "\n\n"
                "## Page %s\n"
                % (index + 1)
            )
            page.dump_text(stream)
        echo0(prefix + "count=%s" % count)

    def collect_pages(self):
        if self._pages is not None:
            raise RuntimeError("_pages already collected")
        self._pages = {}  # key is integer
        self._collect_pages(None, self, None, None, None)


def from_string(data):
    """Parse a string.

    This should have work-alike inputs & outputs as lxml.etree's
    from_string.
    """
    lexer = SGMLLexer(data)
    root = SGMLElementTree()
    root.parse(lexer)
    return root


def from_string_scribus(data, skip_blank=True):
    """Parse a string.

    This should have work-alike inputs & outputs as lxml.etree's
    from_string. Unlike from_string, this returns ScribusDocRoot (a
    subclass which has more features than SGMLElementTree but is
    otherwise identical).
    """
    lexer = SGMLLexer(data, skip_blank=skip_blank)
    root = ScribusDocRoot()
    root.parse(lexer)
    return root


def parse(stream):
    """Parse an open file or stream.

    This should have work-alike inputs & outputs as lxml.etree's
    parse.
    """
    data = stream.read()
    return from_string(data)


def parse_scribus(stream):
    """Parse an open file or stream.

    This should have work-alike inputs & outputs as lxml.etree's parse.
    Unlike parse, this returns ScribusDocRoot (a subclass which has more
    features than SGMLElementTree but is otherwise identical).
    """
    data = stream.read()
    return from_string_scribus(data)


class ScribusProject(object):
    """Manage a scribus file.
    """
    # TODO: Add a get_root() method and get DOCUMENT instead of docroot
    def __init__(self, path):
        self._path = path
        self._original_size = os.path.getsize(self._path)
        # self._data = None  # instead use: self.root._lexer._data
        self.root = None  # self._lexer = None  # formerly _sgml
        self.reload()

    def get_path(self):
        return self._path

    def to_dict(self):
        if self.root is None:
            raise RuntimeError("There is no root. Call parse method first.")
        return self.root.to_dict()

    def reload(self, force=True):
        '''Reload from storage.

        Keyword arguments:
        force -- Reload even if self._data is already present.
        '''
        if ((self.root is None) or (self.root._lexer is None)
                or (self.root._lexer._data is None)) or force:
            echo1('Loading "{}"'.format(self._path))
            with open(self._path) as stream:
                # self._data = stream.read()  # instead:self.root._lexer._data
                # if self._data is not None:
                # echo0("* lexing...")
                # self._lexer = SGMLLexer(self._data)#instead:self.root._lexer
                # echo0("* parsing...")
                # self.root = parse(self._lexer)  # unsorted
                self.root = parse_scribus(stream)
                # ^ mimic lxml: tree = lxml.etree.parse(in_stream)

    def save(self):
        with open(self._path, 'w') as outs:
            outs.write(self._data)

    def move_images(self, old_dir):
        '''
        Move images from the directory that used to contain the SLA
        file.

        Sequential arguments:
        old_dir -- The directory where the SLA file used to reside that
            has the images cited in the SLA file.
        '''
        new_dir = os.path.dirname(os.path.realpath(self._path))
        if os.path.realpath(old_dir) == new_dir:
            raise ValueError(
                'The source and destination directory are the same: "{}".'
                ''.format(old_dir)
            )
        percent_s = None
        in_size = self._original_size
        self.reload(force=False)
        sgml = self._lexer

        inline_images = []
        full_paths = []
        bad_paths = []

        new_data = ""
        done_mkdir_paths = []
        for chunkdef in self._lexer:
            ratio = float(chunkdef['start']) / float(in_size)
            if percent_s is not None:
                sys.stderr.write("\b" * len(percent_s))
                percent_s = None
            percent_s = str(int(ratio * 100)) + "%"
            sys.stderr.write(percent_s)
            sys.stderr.flush()
            chunk = sgml.chunk_from_chunkdef(chunkdef)
            attributes = None
            if chunkdef['context'] == SGMLLexer.START:
                attributes = chunkdef['attributes']
            sub = None
            tagName = chunkdef.get('tagName')
            if tagName is not None:
                if get_verbosity() >= 2:
                    if percent_s is not None:
                        sys.stderr.write("\b" * len(percent_s))
                        percent_s = None
                echo4("tagName=`{}` attributes=`{}`"
                      "".format(tagName, attributes))
                if attributes is not None:
                    # Only opening tags have attributes,
                    #   not closing tags such as </p>.
                    sub = attributes.get('PFILE')
            else:
                if get_verbosity() >= 2:
                    if percent_s is not None:
                        sys.stderr.write("\b" * len(percent_s))
                        percent_s = None
                echo4("value=`{}`".format(chunk))
            isInlineImage = False
            if ((attributes is not None)
                    and (attributes.get('isInlineImage') == "1")):
                isInlineImage = True
                # An inline image...
                # Adds:
                # - ImageData (has base64-encoded data)
                # - inlineImageExt="png"
                # - isInlineImage="1"
                # - ANNAME=" image843"
                # Changes:
                # - PFILE=""
                # - FRTYPE="3"  instead of "0" (always?)
                # - CLIPEDIT="1" instead of "0" (always?)
                inline_stats = {
                    'OwnPage': int(attributes.get('OwnPage')) + 1,
                    'inlineImageExt': attributes.get('inlineImageExt'),
                    'FRTYPE': attributes.get('FRTYPE'),
                    'CLIPEDIT': attributes.get('CLIPEDIT'),
                    # also has ImageData but that is large (base64).
                }
                inline_images.append(inline_stats)
                # ^ pages start at 0 here, but not in GUI.
                sub = None
            if sub is not None:
                if percent_s is not None:
                    sys.stderr.write("\b" * len(percent_s))
                    percent_s = None

                sub_path = os.path.join(old_dir, sub)
                is_full_path = False
                if os.path.realpath(sub) == sub:
                    sub_path = sub
                    full_paths.append(sub)
                    is_full_path = True

                write0('* checking `{}`...'.format(sub_path))
                if isInlineImage:
                    pass
                elif os.path.isfile(sub_path):
                    echo0("OK")
                    new_path = os.path.join(new_dir, sub)
                    dst_parent = os.path.dirname(new_path)
                    if not os.path.isdir(dst_parent):
                        if dst_parent not in done_mkdir_paths:
                            print('mkdir "{}"'.format(dst_parent))
                            done_mkdir_paths.append(dst_parent)
                            os.makedirs(dst_parent)
                    print('mv "{}" "{}"'.format(sub_path, new_path))
                    shutil.move(sub_path, new_path)
                else:
                    echo0("NOT FOUND")
                    bad_paths.append(sub)
                # Update chunk using the modified property:
                chunk = self._lexer.chunk_from_chunkdef(chunkdef)
            new_data += chunk
            # sys.stdout.write(chunk)
            # sys.stdout.flush()
        if percent_s is not None:
            sys.stderr.write("\b" * len(percent_s))
            percent_s = None
        echo0("100%")
        echo1()
        if len(bad_paths) > 0:
            echo1("bad_paths:")
            for bad_path in bad_paths:
                echo1('- "{}"'.format(bad_path))
        if len(full_paths) > 0:
            echo1("full_paths:")
            for full_path in full_paths:
                echo1('- "{}"'.format(full_path))
        if len(inline_images) > 0:
            echo1("inline_images (+1 for GUI numbering):")
            for partial_attributes in inline_images:
                echo1('- "{}"'.format(partial_attributes))

    def unordered_unparsed_dump_text(self, stream):
        '''Dump text (in XML order--for spatial order see SGMLElementTree)
        Dump text from all text fields from the project, regardless of
        order (Use the stored order, not the spatial order).
        '''
        if self._data is None:
            raise ValueError(
                "The file was not parsed."
            )
        echo0("  - dumping...")
        for chunkdef in self._lexer:
            attributes = None
            # tagName = chunkdef.get('tagName')
            # if tagName.lower() != 'itext':
            #     # ch displayable text is usually in ITEXT.
            #     continue
            if chunkdef['context'] == SGMLLexer.START:
                attributes = chunkdef['attributes']
            CH = None
            if attributes is not None:
                CH = attributes.get('CH')
            if CH is None:
                continue
            stream.write(CH + "\n")


def main():
    echo0("You should import this module instead.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
