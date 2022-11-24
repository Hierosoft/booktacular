# -*- coding: utf-8 -*-
'''
Commands:

pull_images
You must specify the old directory where the SLA was.
'''
from __future__ import print_function
from __future__ import division
import sys
import os

import pyscribus.sla as sla
from .find_hierosoft import hierosoft
from hierosoft import (
    echo0,
    echo1,
    echo2,
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


def pull_images(sla_file, old_dir):
    parsed = sla.SLA(sla_file, "1.5.8")
    return 0


def main():
    if len(sys.argv) < 3:
        echo0(__doc__)
        return 1
    return pull_images(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    sys.exit(main())
