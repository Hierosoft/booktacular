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

# from booktacular.find_pyscribus import pyscribus
# import pyscribus.sla as sla
from booktacular.find_hierosoft import hierosoft  # noqa: F401

from hierosoft import (  # noqa: F401
    echo0,
    echo1,
    echo2,
    replace_vars,
    # set_verbosity,
    # get_verbosity,
)

# from booktacular import (
#     REPO_DIR,
# )

from booktacular.morescribus import (
    ScribusProject,
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


'''
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
'''

ERROR_MISSING_ARG = 1
ERROR_BAD_PATH = 2


def pull_images(dst_file, old_dir):
    # EXAMPLE_OUT_FILE = os.path.splitext(dst_file)[0] + ".example-output.sla"
    if not os.path.isfile(dst_file):
        echo0('Error: "{}" does not exist.')
        return ERROR_BAD_PATH
    # set_verbosity(1)
    # echo0('The module will run in the example with verbosity={}.'
    #       ''.format(get_verbosity()))
    if not os.path.isdir(old_dir):
        '''
        echo0('There is no "{}" for checking the move feature, so '
              ' missing files will be checked using relative paths'
              ' (OK if already ready for Scribus,'
              ' since it uses relative paths).')
        '''
        echo0('Error: OLD_DIR "{}" does not exist.'.format(old_dir))
        return ERROR_BAD_PATH
        old_dir = os.path.dirname(dst_file)
    else:
        echo0('Looking for missing files to move from "{}" for "{}"'
              ''.format(old_dir, os.path.split(dst_file)[1]))

    project = ScribusProject(dst_file)
    project.move_images(old_dir)
    # project.save()
    # echo0('Done writing "{}"'.format(project.get_path()))
    return 0


def main():
    # MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
    # REPO_DIR = os.path.dirname(MODULE_DIR)
    EXAMPLE_FILE = "The Path of Resistance.sla"
    OLD_DIR = os.path.join(replace_vars("%CLOUD%"), "Tabletop", "Campaigns",
                           "The Path of Resistance")
    if len(sys.argv) != 3:
        echo0("Error: You must specify the new file and the old directory"
              " to gather files used by the file.")
        if os.path.isdir(OLD_DIR):
            echo0("Such as:")
            echo0('pull_images "{}" "{}"'.format(EXAMPLE_FILE, OLD_DIR))
        return 1
    # dst_file = EXAMPLE_FILE

    return pull_images(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    sys.exit(main())
