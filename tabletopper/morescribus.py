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
import sys
import os
import re
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
    replace_vars,
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


def main():
    echo0("You should import this module instead.")
    MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
    REPO_DIR = os.path.dirname(MODULE_DIR)
    EXAMPLE_FILE = os.path.join(REPO_DIR, "The Path of Resistance.sla")
    EXAMPLE_OUT_FILE = os.path.splitext(EXAMPLE_FILE)[0] + ".example-output.sla"
    OLD_DIR = os.path.join(replace_vars("%CLOUD%"), "Tabletop", "Campaigns",
                           "The Path of Resistance")
    if os.path.isfile(EXAMPLE_FILE):
        set_verbosity(1)
        echo0('The module will run in the example with verbosity={}.'
              ''.format(get_verbosity()))
        if not os.path.isdir(OLD_DIR):
            echo0('There is no "{}" for checking the move feature, so '
                  ' missing files will be checked using relative paths'
                  ' (OK if already ready for Scribus,'
                  ' since it uses relative paths).')
            OLD_DIR = os.path.dirname(EXAMPLE_FILE)
        else:
            echo0('Looking for missing files to move from "{}" for "{}"'
                  ''.format(OLD_DIR, os.path.split(EXAMPLE_FILE)[1]))
        in_size = os.path.getsize(EXAMPLE_FILE)
        static_width = 72
        percent_s = None
        with open(EXAMPLE_FILE, 'r') as ins:
            data = ins.read()
            with open(EXAMPLE_OUT_FILE, 'w') as outs:
                sgml = SGML(data)
                for chunkdef in sgml:
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
                    if sub is not None:
                        if percent_s is not None:
                            sys.stderr.write("\b"*len(percent_s))
                            percent_s = None

                        sub_path = os.path.join(OLD_DIR, sub)
                        write0('* checking `{}`...'.format(sub_path))
                        if len(sub) == 0:
                            # blank image PFILE value
                            pass
                        elif os.path.isfile(sub_path):
                            echo0("OK")
                        else:
                            echo0("NOT FOUND")
                        # Update chunk using the modified property:
                        chunk = sgml.chunk_from_chunkdef(chunkdef)
                    outs.write(chunk)
                    # sys.stdout.write(chunk)
                    # sys.stdout.flush()
            if percent_s is not None:
                sys.stderr.write("\b"*len(percent_s))
                percent_s = None

            echo0('Done writing "{}"'.format(EXAMPLE_OUT_FILE))
    else:
        echo0('The example file was skipped since not found: "{}"'
              ''.format(DEMO_FILE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
