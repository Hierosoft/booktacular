# -*- coding: utf-8 -*-
'''
booktacular.morescribus.compare
-------------------------------

Compare two SLA (Scribus Project) files by only their text. The changes
to the text-only temporary files being compared will not be written
back to the original files.

Usage:
# Typically you would install booktacular and do:
sla-meld <file1.sla> <file2.sla>
# directly use it via
# python3 compare.py <file1.sla> <file2.sla>
'''
from __future__ import print_function
import sys
import os
import tempfile
import subprocess

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


def usage():
    echo0()
    echo0(__doc__)
    echo0()


def meld_sla(paths, tmp_path=None):
    tmpdir = None
    try:
        if tmp_path is None:
            tmpdir = tempfile.TemporaryDirectory()
            tmp_path = tmpdir.name
        if len(paths) != 2:
            raise ValueError("You must provide 2 paths, each to an SLA file.")
        tmp_paths = []
        projects = []
        for path in paths:
            name = os.path.split(path)[1]
            no_ext_name = os.path.splitext(name)[0]
            new_name = "{}.txt".format(no_ext_name)
            this_tmp_path = os.path.join(tmp_path, new_name)
            i = 0
            while this_tmp_path in tmp_paths:
                i += 1
                new_name = "{}-{}.txt".format(no_ext_name, i)
                this_tmp_path = os.path.join(tmp_path, new_name)
            tmp_paths.append(this_tmp_path)
            project = ScribusProject(path)
            projects.append(project)
            with open(this_tmp_path, 'w') as f:
                print('* dumping temp file "{}"'.format(this_tmp_path))
                project.dump_text(f)
        cmd_parts = ["meld", tmp_paths[0], tmp_paths[1]]
        '''
        meldq = None
        meldq = which("meldq")
        if meldq is not None:
            cmd_parts[0] = meldq
        '''
        # process = subprocess.Popen(cmd_parts, shell=False)
        # ^ Popen is non-blocking
        result = subprocess.call(cmd_parts, shell=False)
        echo0("result={}".format(result))
    finally:
        try:
            if tmpdir is not None:
                tmpdir.cleanup()
        except PermissionError:
            pass


def main():
    if len(sys.argv) != 3:
        echo0("Error: You must provide two paths, each to an SLA file.")
        return 1
    paths = sys.argv[1:]
    '''
    if (sys.version_info.major >= 3) and (sys.version_info.minor >= 10):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            tmp_path = tmpdir.name
            meld_sla(paths, tmp_path)
    '''
    meld_sla(paths)
    return 0
