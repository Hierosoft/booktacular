#!/usr/bin/env python
import setuptools
import os

# versionedModule = {}
# versionedModule['urllib'] = 'urllib'
# if sys.version_info.major < 3:
#     versionedModule['urllib'] = 'urllib2'

install_requires = [
    'hierosoft @ git+ssh://git@github.com/Hierosoft/hierosoft.git',
    'pycodetool @ git+ssh://git@github.com/Hierosoft/pycodetool.git',
]

description = (
    "This set of tools is used to manage Scribus files and other source"
    " files for writing books."
)
long_description = description
if os.path.isfile("readme.md"):
    with open("readme.md", "r") as fh:
        long_description = fh.read()

setuptools.setup(
    name='booktacular',
    version='0.5.0',
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3',
        'Operating System :: POSIX :: Linux',
        'License :: Free To Use But Restricted',
        'Topic :: Text Processing :: General',
        'Topic :: Utilities',
    ],
    keywords=('tabletop rpg book scribus'),
    url="https://github.com/Hierosoft/booktacular",
    author="Jake Gustafson",
    author_email='7557867+poikilos@users.noreply.github.com',
    # packages=setuptools.find_packages(),
    packages=['booktacular'],
    include_package_data=True,  # look for MANIFEST.in
    # scripts=['example'],
    # ^ Don't use scripts anymore (according to
    #   <https://packaging.python.org/en/latest/guides
    #   /distributing-packages-using-setuptools
    #   /?highlight=scripts#scripts>).
    # See <https://stackoverflow.com/questions/27784271/
    # how-can-i-use-setuptools-to-generate-a-console-scripts-entry-
    # point-which-calls>
    entry_points={
        'console_scripts': [
            'pull_images=booktacular.pull_images:main',
            'meldsla=booktacular.meldsla:main',
            'dumpslatext=booktacular.dumpslatext:main',
        ],
    },
    install_requires=install_requires,
    #     versionedModule['urllib'],
    # ^ "ERROR: Could not find a version that satisfies the requirement
    #   urllib (from nopackage) (from versions: none)
    #   ERROR: No matching distribution found for urllib"
    test_suite='nose.collector',
    tests_require=['nose', 'nose-cover3'],
    zip_safe=False,  # It can't run zipped due to needing data files.
)
