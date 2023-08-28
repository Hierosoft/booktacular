# -*- coding: utf-8 -*-
'''
This submodule is part of the tabletopper module originally from
<https://github.com/Hierosoft/thepathofresistance>.

Author: Jake "Poikilos" Gustafson

Process SLA files in a similar way as Python's HTMLParser so that you
can safely manipulate the files regardless of version. There is no
value checking, so it is mostly so that client code (such as
pull_images.py or your code that imports this submodule) can do
analysis and mass replacement.

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
  `scribus -py somescript.py --python-arg v`
  -<https://stackoverflow.com/a/33370042/4541104>
'''
from __future__ import print_function
import sys
import os
import re
import shutil
import json
from collections import OrderedDict

if __name__ == "__main__":
    sys.path.insert(
        0,
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    )

from tabletopper.find_hierosoft import hierosoft
# ^ works for submodules too since changes sys.path

from hierosoft import (
    echo0,
    echo1,
    echo2,
    write0,
    write1,
    write2,
    set_verbosity,
    get_verbosity,
)

from tabletopper.find_pycodetool import pycodetool
# ^ works for submodules too since changes sys.path

from pycodetool.parsing import (
    explode_unquoted,
    find_whitespace,
    find_unquoted_even_commented,
)


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

    def __init__(self, data, strict=True):
        self._data = data
        self._chunkdef = None
        self.stack = []
        self.strict = strict

    def chunk_from_chunkdef(self, chunkdef, raw=False):
        '''Get a slice from a chunkdef.

        Args:
            chunkdef (dict): chunk definition that is returned by next
            raw (bool) If True, get the slice from the original data. This
                would happen even if False if not SGMLLexer.START. The raw option
                allows getting the underlying data that existed before
                'attributes' was modified.

        Returns:
            string: The literal SGMLLexer chunk that represents the chunkdef.
                If 'context' is START, the tag will be generated from
                'attributes'! Otherwise, the result is a slice of
                self._data.
        '''
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
            if len(key.strip()) == 0:
                raise ValueError(
                    "A property name must not be blank but got {}"
                    "".format(badchar, key+"="+value)
                )
            for badchar in ["=", " "]:
                if badchar in key:
                    raise ValueError(
                        "A property name must not contain '{}' but got `{}`"
                        "".format(badchar, key+"="+value)
                    )
            if value is None:
                chunk += key
            else:
                badchar = '"'
                if badchar in value:
                    raise ValueError(
                        'A property value must not contain "{}": {}="{}"'
                        ''.format(badchar, key, value)
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

    def next(self):
        """Lex (not parse) the next chunk, which can be start, content, or end

        For context and making a tree, see the "parse" method.
        """
        previous = self._chunkdef
        self._chunkdef = {}

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
            raise StopIteration()
        self._chunkdef['start'] = start
        if self._data[start:start+2] == "</":
            self._chunkdef['context'] = SGMLLexer.END
        elif self._data[start] == "<":
            self._chunkdef['context'] = SGMLLexer.START
        elif self._data[start:start+1] == ">":
            echo0('Warning: unexpected > at character number {}'
                  ''.format(start))
            self._chunkdef['context'] = SGMLLexer.CONTENT
        else:
            self._chunkdef['context'] = SGMLLexer.CONTENT

        if self._chunkdef['context'] == SGMLLexer.CONTENT:
            self._chunkdef['end'] = self._data.find("<", start+1)
            if self._chunkdef['end'] < 0:
                self._chunkdef['end'] = len(self._data)
                content = self._data[self._chunkdef['start']:]
                if (len(content.strip()) != 0) or (len(self.stack) > 0):
                    message = (
                        'Warning: The file ended before a closing tag'
                        ' after `{}`.'
                        ''.format(
                            content,
                            self._stack_tagwords(),
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
                start+1,
                quote_marks='"',
            )
            if self._chunkdef['end'] < start+1:
                raise RuntimeError(
                    "The '<' at {} wasn't closed."
                    "".format(start)
                )
            self._chunkdef['end'] += 1  # The ender is exclusive so include '>'.
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
                # prop_absstart = self._chunkdef['start']
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
                            value = statement[sign_i+1:].strip()
                            if ((len(value) >= 2) and (value[0] == '"')
                                    and (value[-1] == '"')):
                                value = value[1:-1]
                            attributes[key] = value
                        else:
                            # It is a value-less property.
                            key = statement
                            attributes[key] = None
                else:
                    echo2("There are no attributes in `{}`"
                          "".format(chunk[:30]+"..."))
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
                                self._stack_tagwords(),
                            )
                        )
                elif self._chunkdef['tagName'] != self.stack[-1]['tagName']:
                    if self.strict:
                        raise SyntaxError(
                            "{} ended at {} before the expected {}"
                            "".format(
                                self._chunkdef['tagName'],
                                start,
                                self._stack_tagwords(),
                            )
                        )
                else:
                    del self.stack[-1]
        return self._chunkdef

    def _stack_tagwords(self):
        """Get a list of the current tagwords that are still open.

        Returns:
            list: tagword strings from innermost to outermost.
        """
        results = []
        for i in reversed(range(0, len(self.stack))):
            results.append(self.stack[i]['tagName'])
        return results


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

    def to_dict(self, enable_locations=True):
        result = OrderedDict()
        for key in type(self).KEYS:
            if key == "value":
                result[key] = self.value
            elif key == "tagName":
                result[key] = self.tagName
            elif key == "self_closer":
                if self.self_closer is not None:
                    result[key] = self.tagName
            elif (key in ("start", "end")) and not enable_locations:
                pass
            elif key == "context":
                if type(self).__name__ == "SGMLText":
                    result[key] = SGMLLexer.CONTENT
                elif type(self).__name__ == "SGMLNode":
                    result[key] = SGMLLexer.START
                elif type(self).__name__ == "SGMLElementTree":
                    # result[key] = SGMLLexer.START
                    pass
                else:
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

    def _dump_text(self, stream, parent, root, pos_node, page_node):
        # if node['tagName'].upper() == "PAGEOBJECT":

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
            if XPOS is not None:
                if YPOS is not None:
                    pos_node = self
                else:
                    raise NotImplementedError("XPOS without YPOS at %s"
                                              % self.start)
        else:
            if pos_node:
                XPOS = pos_node.attributes['XPOS']
                YPOS = pos_node.attributes['YPOS']
            if page_node:
                OwnPage = page_node.attributes['OwnPage']
        tagName = None
        tagNameUpper = None
        if hasattr(self, 'tagName'):
            tagName = self.tagName
            tagNameUpper = tagName.upper()
        children = None
        if hasattr(self, 'children'):
            children = self.children

        # if tagName.lower() != 'ITEXT':
        #     # CH attribute (displayable text) is usually in ITEXT.
        #     return
        if CH is not None:
            stream.write(CH + "\n")
        if children is None:
            return
        for child in children:
            child._dump_text(stream, self, root, pos_node, page_node)

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
                    for attr_key, attr_value in value.items():
                        self.attributes[attr_key] = attr_value
                elif key == 'value':  # TODO: eliminate this if never occurs
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

    def populate(self, lexer):
        """
        Args:
            lexer (SGMLLexer): The SGMLLexer
        """
        try:
            while True:
                chunkdef = lexer.next()
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
                            child.populate(lexer)
                        # else self-closing so next child also belongs to self
                elif context == SGMLLexer.END:
                    # return to parent
                    break
                else:
                    raise NotImplementedError("Unknown context: %s"
                                              % context)
        except StopIteration:
            pass


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

    def dump_text(self, stream):
        '''Dump all text in spatial order, respecting up to 2 columns.

        Also respect multiple sections per page (if there is a box the
        width of the whole page, the column order automatically changes
        - from: left, right
        - to: top-left, top-right, full-width-box, bottom-left, bottom-right
        '''
        if self._lexer is None:
            raise RuntimeError("you must lex and parse first.")

        if self.children is None:
            raise RuntimeError("you must parse first.")

        # TODO: sort in spatial order
        for sub in self.children:
            sub._dump_text(stream, self, self, None, None)

    def parse(self, lexer):
        self._lexer = lexer
        if lexer._data is None:
            raise ValueError(
                "The file was not lexed. See (or use) morescribus.parse"
                " or morescribus.from_string for correct usage of object"
            )
        echo0("  - parsing...")
        min_page = None
        max_page = None
        self.populate(lexer)
        # self.children = self._parse(lexer, self, None, None, None)


def from_string(data):
    """Parse a string.

    This should have work-alike inputs & outputs as lxml.etree's
    from_string.
    """
    lexer = SGMLLexer(data)
    root = SGMLElementTree()
    root.parse(lexer)
    return root


def parse(stream):
    """Parse an open file or stream.

    This should have work-alike inputs & outputs as lxml.etree's
    parse.
    """
    data = stream.read()
    return from_string(data)


class ScribusProject(object):
    def __init__(self, path):
        self._path = path
        self._original_size = os.path.getsize(self._path)
        # self._data = None  # instead use: self.root._lexer._data
        self.root = None  # self._lexer = None  # formerly _sgml
        self.reload()

    def get_path(self):
        return self._path

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
                # self.root = parse(self._lexer)
                self.root = parse(stream)
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
                sys.stderr.write("\b"*len(percent_s))
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
                        sys.stderr.write("\b"*len(percent_s))
                        percent_s = None
                echo2("tagName=`{}` attributes=`{}`"
                      "".format(tagName, attributes))
                if attributes is not None:
                    # Only opening tags have attributes,
                    #   not closing tags such as </p>.
                    sub = attributes.get('PFILE')
            else:
                if get_verbosity() >= 2:
                    if percent_s is not None:
                        sys.stderr.write("\b"*len(percent_s))
                        percent_s = None
                echo2("value=`{}`".format(chunk))
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
                    sys.stderr.write("\b"*len(percent_s))
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
            sys.stderr.write("\b"*len(percent_s))
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

    def unordered_dump_text(self, stream):
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
            tagName = chunkdef.get('tagName')
            # if tagName.lower() != 'itext':
            #     # CH displayable text is usually in ITEXT.
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
