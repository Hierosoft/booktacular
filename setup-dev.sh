#!/bin/bash
missing=""
if [ ! -f "booktacular/__init__.py" ]; then
    >&2 echo "`pwd` does not seem to be the booktacular repo. cd to the repo containing \"booktacular/__init__.py\" first"
    exit 1
fi
if [ ! -d "../hierosoft" ]; then
    missing="$missing ../hierosoft"
fi
if [ ! -d "../pycodetool" ]; then
    missing="$missing ../pycodetool"
fi
if [ ! -z "$missing" ]; then
    >&2 echo "Error: Missing$missing. This script is only for installing the dependencies in editable mode. Clone missing repo(s) into `realpath ..` and try again."
    exit 1
fi
if [ -z "$PIP" ]; then
    PIP=.venv/bin/pip
    if [ ! -f "$PIP" ]; then
        >&2 echo "Error: Missing \"$PIP\". Cannot continue."
        exit 1
    fi
fi
$PIP uninstall -y hierosoft
$PIP install -e ../hierosoft || exit 1
# pycodetool must be uninstalled *after* hierosoft is *installed* since
#   hierosoft installs the git version:
$PIP uninstall -y pycodetool
$PIP install -e ../pycodetool || exit 1
