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
    >&2 echo "[$0] Error: Missing$missing. This script is only for installing the dependencies in editable mode. Clone missing repo(s) into `realpath ..` and try again."
    exit 1
fi
if [ -z "$PIP" ]; then
    PIP=.venv/bin/pip
    if [ ! -f "$PIP" ]; then
        >&2 echo "Error: Missing \"$PIP\". Cannot continue."
        exit 1
    fi
fi

>&2 echo "[$0] * uninstalling old booktacular..."
$PIP uninstall -y booktacular || exit 1

>&2 echo "[$0] install --no-deps -e .[dev]  # booktacular itself..."
$PIP install --no-deps -e .[dev] || exit 1

if [ -f ../hierosoft/hierosoft/__init__.py ]; then
    >&2 echo "[$0] * using local version of hierosoft..."
    $PIP uninstall -y hierosoft || exit 1
    $PIP install --no-deps -e ../hierosoft || exit 1
    # --no-deps: hierosoft is tolerant of missing deps
    #   (To avoid psutil dep, don't use processwrapper nor moreweb;
    #   To avoid tinytag dep, don't use moremeta)
else
    >&2 echo "[$0] INFO: Using hierosoft from dev dependencies."
fi

# pycodetool must be uninstalled *after* hierosoft is *installed* since
#   hierosoft installs the git version:
if [ -f ../pycodetool/pycodetool/__init__.py ]; then
    >&2 echo "[$0] * using local version of pycodetool..."
    $PIP uninstall -y pycodetool || exit 1
    $PIP install --no-deps -e ../pycodetool || exit 1
    # --no-deps: Only requires hierosoft, so already present in this case.
else
    >&2 echo "[$0] INFO: Using hierosoft from dev dependencies."
fi

if [ -f ../pyinkscape/pyinkscape/__init__.py ]; then
    >&2 echo "[$0] * using local version of pyinkscape..."
    $PIP uninstall -y pyinkscape || exit 1
    $PIP install -e ../pyinkscape || exit 1
else
    >&2 echo "[$0] INFO: Using pyinkscape from PyPI."
fi