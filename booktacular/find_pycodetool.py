# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import os
import platform

REPO_USER = "poikilos"
REPO_NAME = "pycodetool"
MODULE_NAME = "pycodetool"  # See also import pycodetool statements

GIT_SERVER = "https://github.com"

CALLER_NAME = os.path.split(sys.argv[0])[1]
profile = os.environ.get('HOME')
if platform.system() == "Windows":
    profile = os.environ['USERPROFILE']

_TRY_REPO = os.path.join(profile, "git", REPO_NAME)
_TRY_MODULE = os.path.join(_TRY_REPO, MODULE_NAME)

MY_MODULE = os.path.dirname(os.path.abspath(__file__))
MY_REPO = os.path.dirname(MY_MODULE)
MY_REPOS = os.path.dirname(MY_REPO)

_NEARBY_REPO = os.path.join(MY_REPOS, REPO_NAME)


def echo0(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


if os.path.isfile(os.path.join(_NEARBY_REPO, MODULE_NAME, "__init__.py")):
    sys.path.insert(0, _NEARBY_REPO)
    echo0("[{}] using nearby {}".format(CALLER_NAME, _NEARBY_REPO))
elif os.path.isdir(_TRY_MODULE):
    sys.path.insert(0, _TRY_REPO)
    echo0("[{}] using git {}".format(CALLER_NAME, _TRY_REPO))
else:
    pass
    # use the one in the python path (or fail)
    # print("There is no {}".format(os.path.join(thisRepo, MODULE_NAME)))

# import pycodetool  # noqa: E402,F401 type: ignore

try:
    import pycodetool  # noqa: E402,F401 type: ignore
except ImportError as ex:
    echo0("sys.path={}".format(sys.path))
    echo0(str(ex))
    echo0('"{}" is part of {}. You must install the repo:'
          ''.format(CALLER_NAME, REPO_NAME))
    echo0("# Clone it then:")
    echo0("python3 -m pip install {}".format(MODULE_NAME))
    echo0('# or just put it in a directory near here such as via:')
    echo0('  git clone {}/{}/{}'
          ' "{}"'.format(GIT_SERVER, REPO_USER, REPO_NAME, _NEARBY_REPO))
    sys.exit(1)
