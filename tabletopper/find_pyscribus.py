# -*- coding: utf-8 -*-
from __future__ import print_function
import re
import sys
import os
import platform

REPO_USER = "Poikilos"
REPO_NAME = "pyscribus"
MODULE_NAME = "pyscribus"  # See also import pyscribus statements

source_sub_name = "source"  # The module is within this sub in the repo.
# ^ Set to None if MODULE_NAME is a child of the repo as is common.

GIT_SERVER= "https://framagit.org"

CALLER_NAME = os.path.split(sys.argv[0])[1]
profile = os.environ.get('HOME')
if platform.system() == "Windows":
    profile = os.environ['USERPROFILE']

tryRepo = os.path.join(profile, "git", REPO_NAME)
tryModule = os.path.join(tryRepo, MODULE_NAME)

MY_MODULE = os.path.dirname(os.path.abspath(__file__))
MY_REPO = os.path.dirname(MY_MODULE)
MY_REPOS = os.path.dirname(MY_REPO)

nearbyRepo = os.path.join(MY_REPOS, REPO_NAME)


def echo0(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


if sys.version_info.major < 3:
    # FileNotFoundError = IOError
    ModuleNotFoundError = ImportError

try:
    import pyscribus
    # Don't mess with the path at all if it already works.
    echo0("[{}] using sys.path's {}".format(CALLER_NAME, pyscribus.__file__))
except ModuleNotFoundError:
    nearbyModules = nearbyRepo
    if source_sub_name is not None:
        nearbyModules = os.path.join(nearbyModules, source_sub_name)
    nearbyModulePath = os.path.join(nearbyModules, MODULE_NAME)
    echo0('* checking for __init__.py in "{}"'.format(nearbyModulePath))
    if os.path.isfile(os.path.join(nearbyModulePath, "__init__.py")):
        sys.path.insert(0, nearbyModules)
        echo0("[{}] using nearby {}".format(CALLER_NAME, nearbyRepo))
    elif os.path.isdir(tryModule):
        sys.path.insert(0, tryRepo)
        echo0("[{}] using git {}".format(CALLER_NAME, tryRepo))
    else:
        pass
        # use the one in the python path (or fail)
        # print("There is no {}".format(os.path.join(thisRepo, MODULE_NAME)))

    import pyscribus

    try:
        import pyscribus
    except ImportError as ex:
        echo0("sys.path={}".format(sys.path))
        echo0(str(ex))
        echo0('"{}" is part of {}. You must install the repo:'
              ''.format(CALLER_NAME, REPO_NAME))
        echo0("# Clone it then:")
        echo0("python3 -m pip install {}".format(MODULE_NAME))
        echo0('# or just put it in a directory near here such as via:')
        echo0('  git clone {}/{}/{}'
              ' "{}"'.format(GIT_SERVER, REPO_USER, REPO_NAME, nearbyRepo))
        sys.exit(1)
