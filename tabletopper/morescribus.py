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
# from collections import OrderedDict

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


class SGML:
    '''
    This is a generator that provides chunkdefs where each chunk is one
    of the CONTENT_ types. No context such as tag ancestors is
    calculated within this class.

    When modifying a value of 'properties', ensure that any double quote
    ('"') inside of is converted to "&quot;".

    Private attributes:
    _data -- The data (set via the feed method)

    Returns:
    chunkdef dictionary where start and end define a slice of the data,
    and 'context' is the CONTEXT_ constant which defines what type of
    data is at the slice. The slice can be obtained by passing the
    returned slice to the chunk_from_chunkdef() method.
    '''

    START = "start"  # the return is a start tag such as <p>
    END = "end"  # the return is an end tag such as </p>
    CONTENT = "content"  # the return is content between tags

    def __init__(self, data):
        self._data = data
        self._chunkdef = None

    def chunk_from_chunkdef(self, chunkdef, raw=False):
        '''
        Get a slice from a chunkdef that is returned by next. If
        'context' is START, the tag will be generated from
        'properties' instead of the slice!

        Keyword arguments:
        raw -- If True, get the slice from the original data. This
            would happen even if False if not SGML.START. The raw option
            allows getting the underlying data that existed before
            'properties' was modified.
        '''
        if (chunkdef['context'] != SGML.START) or raw:
            if (not raw) and chunkdef.get('properties') is not None:
                raise ValueError(
                    'A {} tag should not have properties.'
                    ''.format(chunkdef['context'])
                )
            return self._data[chunkdef['start']:chunkdef['end']]
        chunk = "<" + chunkdef['tag']
        # OrderedDict or Python (2.7+? or) 3.7+ must be used to maintain
        # the order:
        for key, value in chunkdef['properties'].items():
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
        if chunkdef.get('self-closing') is not None:
            chunk += chunkdef['self-closing'] + ">"
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
            self._chunkdef['context'] = SGML.END
        elif self._data[start] == "<":
            self._chunkdef['context'] = SGML.START
        elif self._data[start:start+1] == ">":
            echo0('Warning: unexpected > at character number {}'
                  ''.format(start))
            self._chunkdef['context'] = SGML.CONTENT
        else:
            self._chunkdef['context'] = SGML.CONTENT

        if self._chunkdef['context'] == SGML.CONTENT:
            self._chunkdef['end'] = self._data.find("<", start+1)
            if self._chunkdef['end'] < 0:
                self._chunkdef['end'] = len(self._data)
                echo0('Warning: The file ended before a closing tag'
                      ' after `{}`.'
                      ''.format(self._data[self._chunkdef['start']:]))
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
            if self._chunkdef['context'] == SGML.START:
                props_end = len(chunk) - 1  # exclude '>'.
                if chunk.endswith("/>"):
                    props_end -= 1
                    self._chunkdef['self-closing'] = "/"
                elif chunk.endswith("?>"):
                    props_end -= 1
                    self._chunkdef['self-closing'] = "?"
                    # Such as `<?xml version="1.0" encoding="UTF-8"?>`

                # self._chunkdef['properties'] = OrderedDict()
                # As of Python 3.7, dict order is guaranteed to be the
                #   insertion order, but OrderedDict
                #   is still required to support reverse (and
                #   OrderedDict's own move_to_end method).
                #   -<https://stackoverflow.com/a/50872567/4541104>
                self._chunkdef['properties'] = {}
                properties = self._chunkdef['properties']
                # prop_absstart = self._chunkdef['start']
                props_start = find_whitespace(chunk, 0)
                if props_start > -1:
                    self._chunkdef['tag'] = chunk[1:props_start].strip()
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
                            properties[key] = value
                        else:
                            # It is a value-less property.
                            key = statement
                            properties[key] = None
                else:
                    echo2("There are no properties in `{}`"
                          "".format(chunk[:30]+"..."))
                    # There are no properties.
                    self._chunkdef['tag'] = chunk[1:props_end].strip()
                    # ^ 1 to avoid "<" and -1 to avoid ">"
            elif self._chunkdef['context'] == SGML.END:
                self._chunkdef['tag'] = chunk[2:-1].strip()
                # ^ 2 to avoid both "<" and "/" since an SGML.END.

        return self._chunkdef


class ScribusProject:
    def __init__(self, path):
        self._path = path
        self._original_size = os.path.getsize(self._path)
        self._data = None
        self._sgml = None
        self.reload()

    def get_path(self):
        return self._path

    def reload(self, force=True):
        '''
        Reload from storage.

        Keyword arguments:
        force -- Reload even if self._data is already present.
        '''
        if (self._data is None) or force:
            echo1('Loading "{}"'.format(self._path))
            with open(self._path) as f:
                self._data = f.read()
                # if self._data is not None:
                echo0("* parsing...")
                self._sgml = SGML(self._data)

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
        sgml = self._sgml

        inline_images = []
        full_paths = []
        bad_paths = []

        new_data = ""
        done_mkdir_paths = []
        for chunkdef in self._sgml:
            ratio = float(chunkdef['start']) / float(in_size)
            if percent_s is not None:
                sys.stderr.write("\b"*len(percent_s))
                percent_s = None
            percent_s = str(int(ratio * 100)) + "%"
            sys.stderr.write(percent_s)
            sys.stderr.flush()
            chunk = sgml.chunk_from_chunkdef(chunkdef)
            properties = None
            if chunkdef['context'] == SGML.START:
                properties = chunkdef['properties']
            sub = None
            tag = chunkdef.get('tag')
            if tag is not None:
                if get_verbosity() >= 2:
                    if percent_s is not None:
                        sys.stderr.write("\b"*len(percent_s))
                        percent_s = None
                echo2("tag=`{}` properties=`{}`"
                      "".format(tag, properties))
                if properties is not None:
                    # Only opening tags have properties,
                    #   not closing tags such as </p>.
                    sub = properties.get('PFILE')
            else:
                if get_verbosity() >= 2:
                    if percent_s is not None:
                        sys.stderr.write("\b"*len(percent_s))
                        percent_s = None
                echo2("content=`{}`".format(chunk))
            isInlineImage = False
            if ((properties is not None)
                    and (properties.get('isInlineImage') == "1")):
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
                    'OwnPage': int(properties.get('OwnPage')) + 1,
                    'inlineImageExt': properties.get('inlineImageExt'),
                    'FRTYPE': properties.get('FRTYPE'),
                    'CLIPEDIT': properties.get('CLIPEDIT'),
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
                chunk = sgml.chunk_from_chunkdef(chunkdef)
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
            for partial_properties in inline_images:
                echo1('- "{}"'.format(partial_properties))

    def dump_text(self, stream):
        '''
        Dump text from all text fields from the project, regardless of
        order (Use the stored order, not the spatial order).
        '''
        if self._data is None:
            raise ValueError(
                "The file was not parsed."
            )
        echo0("  - dumping...")
        for chunkdef in self._sgml:
            properties = None
            tag = chunkdef.get('tag')
            # if tag.lower() != 'itext':
            #     # CH displayable text is usually in ITEXT.
            #     continue
            if chunkdef['context'] == SGML.START:
                properties = chunkdef['properties']
            CH = None
            if properties is not None:
                CH = properties.get('CH')
            if CH is None:
                continue
            stream.write(CH + "\n")


def main():
    echo0("You should import this module instead.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
