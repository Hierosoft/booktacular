# -*- coding: utf-8 -*-
'''
pull_images
-----------

This script moves images that the SLA file cites from a different
directory where it has no missing image errors to the current directory,
to fix current missing image errors.

Usage:
pull_images <SLA file> <old directory>

'''
from __future__ import print_function
from __future__ import division
import sys
import os

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tabletopper.find_pyscribus import pyscribus
import pyscribus.sla as sla
from tabletopper.find_hierosoft import hierosoft
from hierosoft import (
    echo0,
    echo1,
    echo2,
)

from hierosoft.simpleargs import (
    SimpleArgs,
)

from hierosoft.moreweb import (
    HTMLParser,  # debug only (for testing hierosoft issue #3)
)

makedir_logged_lines = set()


def move_safe(src, dst):
    parent_dir = os.path.dirname(dst)
    if not os.path.isdir(parent_dir):
        msg = 'mkdir -p "{}"'.format(parent_dir)
        if msg not in makedir_logged_lines:
            makedir_logged_lines.add(msg)
            print(msg)
        # os.makedirs(parent_dir)
    print('mv "{}" "{}"'.format(src, dst))
    # shutil.move(src, dst)



def pull_images(options):
    echo0("options={}".format(options))
    old_dir = options['old_dir']
    sla_file = options['sla_file']

    parsed = sla.SLA(sla_file, "1.5.8")
    # ^ fails with "pyscribus.exceptions.InvalidDim: Pica points must
    #   not be inferior to 0." See
    #   <https://framagit.org/etnadji/pyscribus/-/issues/1>
    #   (See also unrelated
    #   <http://etnadji.fr/pyscribus/guide/en/psm.html>)

    return 0


def main():
    '''
    if len(sys.argv) < 3:
        echo0()
        echo0()
        echo0(__doc__)
        echo0("Error: You must specify the old directory"
              " where the SLA was before moving it.")
        return 1
    '''
    sequential_keys = ['sla_file', 'old_dir']
    simpleargs = SimpleArgs(None,
        sequential_keys=sequential_keys,
        required=sequential_keys,
        # flags = ['--pyscribus'],
        usage_docstring=__doc__,
    )
    try:
        simpleargs.collect()
    except Exception as ex:
        simpleargs.usage()
        echo0("Error: {}".format(ex))
        return 1

    return pull_images(simpleargs.options)


if __name__ == "__main__":
    sys.exit(main())
