# -*- coding: utf-8 -*-
'''
dumper
------

dump sla as text.

Usage:
# If you install booktacular you can do:
sla-dump <file.sla>
'''
from __future__ import print_function
import sys
import os
import tempfile
import shutil
from pprint import pformat

from booktacular.find_hierosoft import hierosoft  # noqa: F401
# ^ also works for submodules since changes sys.path

from hierosoft import (  # noqa: F401
    echo0,
    echo1,
    echo2,
    replace_vars,
    # set_verbosity,
    # get_verbosity,
    which,
)

from booktacular.morescribus import (
    ScribusProject,
)

if sys.version_info.major < 3:
    FileNotFoundError = IOError
    ModuleNotFoundError = ImportError


def usage():
    echo0()
    echo0(__doc__)
    echo0()


def dump_sla_text(src_path, dst_path, tmp_dir=None):
    tmpdir = None
    name = os.path.split(src_path)[1]
    no_ext_name, new_dot_ext = os.path.splitext(name)
    try:
        if tmp_dir is None:
            tmpdir = tempfile.TemporaryDirectory()
        tmp_dir_path = tmpdir.name

        name = os.path.split(src_path)[1]
        no_ext_name = os.path.splitext(name)[0]
        new_name = "{}{}".format(no_ext_name, new_dot_ext)
        tmp_path = os.path.join(tmp_dir_path, new_name)
        # i = 0
        # tmp_paths = list(os.listdir(tmpdir))
        # while tmp_path in tmp_paths:
        #     i += 1
        #     new_name = "{}-{}{}".format(no_ext_name, i, new_dot_ext)
        #     tmp_path = os.path.join(tmp_path, new_name)
        project = ScribusProject(src_path)
        # write to a tmp file to ensure a crash doesn't cause a
        #   partial write to dst_path!
        with open(tmp_path, 'w') as stream:
            print('* dumping temp file "{}"'.format(tmp_path))
            # project.root.dump_text_unsorted(stream)
            project.root.dump_text(stream)
        if os.path.isfile(dst_path):
            print("* removing old %s" % pformat(dst_path))
            os.remove(dst_path)
        print("* saving to %s" % pformat(dst_path))
        shutil.move(tmp_path, dst_path)
        # echo0("Writing json...")
        # json_name = "{}.json".format(no_ext_name)
        # tmp_json_path = os.path.join(tmp_dir_path, json_name)
        # json_dst = os.path.join(os.path.dirname(dst_path), json_name)
        # with open(tmp_json_path, 'w') as json_stream:
        #     import json
        #     json.dump(project.to_dict(), json_stream)
        # shutil.move(tmp_json_path, json_dst)
    finally:
        try:
            if tmpdir is not None:
                tmpdir.cleanup()
        except PermissionError:
            pass


MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(MODULE_DIR)
try_file = "The Path of Resistance.sla"
src_path = None


def main():
    """This accepts a file.

    For the one that automatically uses the book, use
    dump_book1_text instead.
    """
    if len(sys.argv) > 1:
        if not os.path.isfile(sys.argv[1]):
            raise FileNotFoundError(sys.argv[1])
    elif os.path.isfile(try_file):
        print("* using detected %s" % pformat(try_file))
        src_path = try_file
    if src_path is None:
        raise FileNotFoundError(
            "You must have %s (normal if running from repo)"
            " or specify an sla file."
            "" % pformat(try_file)
        )
    if len(sys.argv) > 2:
        dst_path = sys.argv[2]
    else:
        dst_dir, name = os.path.split(src_path)
        name_no_ext, _ = os.path.splitext(name)
        dst_name = name_no_ext + ".md"
        dst_path = os.path.join(dst_dir, dst_name)
    '''
    if (sys.version_info.major >= 3) and (sys.version_info.minor >= 10):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            tmp_path = tmpdir.name
            meld_sla(paths, tmp_path)
    '''
    dump_sla_text(src_path, dst_path)
    return 0


def dump_book1_text():
    """Unlike main, this alternative CLI main always uses the book.

    This one should be used instead of main for batch operations in the repo
    of The Path of Resistance.
    """
    if not os.path.isfile(try_file):
        raise FileNotFoundError(
            "You must have %s (normal if running from repo)"
            " or specify an sla file."
            "" % pformat(try_file)
        )
    src_path = try_file
    dst_dir, name = os.path.split(src_path)
    name_no_ext, _ = os.path.splitext(name)
    dst_name = name_no_ext + ".md"
    dst_path = os.path.join(dst_dir, dst_name)
    '''
    if (sys.version_info.major >= 3) and (sys.version_info.minor >= 10):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            tmp_path = tmpdir.name
            meld_sla(paths, tmp_path)
    '''
    dump_sla_text(src_path, dst_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
