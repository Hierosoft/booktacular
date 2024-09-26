'''
# See https://wiki.scribus.net/canvas/Command_line_scripts
Produce a PDF for the SLA passed as a parameter.
Use the same file name and replaces the .sla extension with .pdf

usage:
scribus -g -ns -py step1.scribus.py
'''
import copy
import json
import os
import shutil
import sys
from datetime import datetime

# if not scribus.haveDoc():
#     raise Exception("Error: No document.")
# name_no_ext = os.path.splitext(scribus.getDocName())[0]
# ^ only raise or open if a document file arg was expected to be sent to
#   scribus


def echo0(*args, **kwargs):
    kwargs['file'] = sys.stderr
    print(*args, **kwargs)


running_in_scribus = False
try:
    import scribus  # type: ignore
    running_in_scribus = True
    # In this case, it is running within Scribus.
except ModuleNotFoundError:
    echo0("INFO: {} is being imported as module since not running in Scribus."
          "".format(os.path.basename(os.path.realpath(__file__))))

if sys.version_info.major < 3:
    ModuleNotFoundError = ImportError


my_pretty_name = "booktacular export_all.py"
'''
HOME = None
if platform.system() == "Windows":
    HOME = os.environ['USERPROFILE']
else:
    HOME = os.environ['HOME']
'''
sysdirs = {}
try:
    sysdirs['HOME'] = os.environ['USERPROFILE']
except KeyError:
    sysdirs['HOME'] = os.environ['HOME']


def platform_system():
    """The platform module is not in scribus' env,
    so examine special folders.

    See also python3.12/site-packages/pip/_vendor/platformdirs/unix.py
    """
    try_appdata = os.path.join(sysdirs['HOME'], "AppData")
    try_config = os.path.join(sysdirs['HOME'], ".config")
    try_library = os.path.join(sysdirs['HOME'], "Library")
    if os.path.isdir("C:\\Windows"):
        return "Windows"
    # but C:\Windows is not always the install directory, so:
    if 'USERPROFILE' in os.environ:
        if not os.path.exists(try_appdata):
            if os.path.exists(try_library):
                echo0("OS was not detected since USERPROFILE was set"
                      " but there is no \"{}\". Assuming Darwin (macOS)"
                      " since found \"{}\""
                      .format(try_appdata, try_library))
                return "Darwin"
            if os.path.exists(try_config):
                echo0("OS was not detected since USERPROFILE was set"
                      " but there is no \"{}\". Assuming Linux"
                      " since found \"{}\" and not \"{}\""
                      .format(try_appdata, try_config, try_library))
                return "Linux"
            echo0("OS was not detected. Assuming Windows since no: {}"
                  .format([try_config, try_library]))
        return "Windows"
    if os.path.exists(try_library):
        return "Darwin"
    return "Linux"


if platform_system() == "Darwin":
    sysdirs['APPDATA'] = os.path.join(sysdirs['HOME'], "Library",
                                      "Application Support")
elif platform_system() == "Windows":
    sysdirs['APPDATA'] = os.environ['APPDATA']
else:
    sysdirs['APPDATA'] = os.path.join(sysdirs['HOME'], ".config")

MY_CONFIGS = os.path.join(sysdirs['APPDATA'], "booktacular")
MY_CONFIG = os.path.join(MY_CONFIGS, "booktacular.json")

DEFAULT_SLA_PATH = None
DEFAULT_SNAPSHOTS_PATH = None

DEFAULT_PUBLISH_CONFIG = {
    'morescribus': {
        'scribus-project': DEFAULT_SLA_PATH,
        'release-dir': DEFAULT_SNAPSHOTS_PATH,
    }
}
PUBLISH_CONFIG = None


'''
# - 1.4 has transparency ?? (<https://en.wikipedia.org/wiki/History_of_PDF>)
#   "not allowed" according to <https://www.prepressure.com/pdf/basics/pdfx-3>.
# - "PDF/X-3 files are regular PDF 1.3 or PDF 1.4 files."??
#   "live transparency is not allowed in PDF 1.4 files."
#   (<https://www.prepressure.com/pdf/basics/pdfx-3>)
# - "PDF/X-4 files are regular PDF 1.6 files."
#   "transparency is allowed" (<https://www.prepressure.com/pdf/basics/pdfx-4>)


enum Version
{
    PDF_13  = 13,
    PDF_14  = 14,
    PDF_15  = 15,
    PDF_16  = 16,
    PDF_X1a = 11,
    PDF_X3  = 12,
    PDF_X4  = 10,
    PDFVersion_Min = 10,
    PDFVersion_Max = 16,
};
# ^ from <https://github.com/scribusproject/scribus/blob/
#   41d56c1dcaa4964ab2bddb4b0af45c208536a319/scribus/pdfversion.h#L14>
'''
# ^ version is used below:

EXPORT_FORMATS = {
    'print': {
        # destination is set dynamically further down but during module load.
        'version': 11,
        'resolution': 300,
        'downsample': 300,
        'compress': True,
        'compressmtd': 2,
        # ^ Compression method.  0:Automatic  1:JPEG  2:zip  3:None.
        'quality': 0,
        # ^ Image quality 0:Maximum  1:High  2:Medium  3:Low  4:Minimum
        'bookmarks': False,
        'useDocBleeds': True,
        'fontEmbedding': 1,
        # ^ 0: Embed fonts, 1:Outline fonts, 2:Don't embed any font
        # See FontEmbedding in <https://github.com/scribusproject/scribus/blob/
        # 34e45f567643b813b323e2f3248d19718293d68b/scribus/plugins/
        #     scriptplugin/objpdffile.cpp>:
        # TODO: 'section_3_start': 1,
        'first': 3,
        'last': 167,  # inclusive (NOTE: add 1 for exclusive range function)
    },
    'digital': {
        # destination is set dynamically further down but during module load.
        'version': 10,
        'resolution': 150,
        'downsample': 150,
        'compress': True,
        'compressmtd': 1,
        'quality': 0,
        'bookmarks': False,
        'useDocBleeds': False,
        'fontEmbedding': 0,
        # TODO: 'section_3_start': 21,
    },
}


def save_config():
    my_configs = os.path.dirname(MY_CONFIG)
    if not os.path.isdir(my_configs):
        os.makedirs(my_configs)
    tmp_path = MY_CONFIG + ".tmp"
    # Use a tmp file to prevent a corrupt/blank file.
    with open(tmp_path, 'w') as stream:
        json.dump(PUBLISH_CONFIG, stream, indent=2, sort_keys=True)
    shutil.move(tmp_path, MY_CONFIG)
    echo0('[export_all save_config] saved "%s"' % MY_CONFIG)


def load_config():
    global PUBLISH_CONFIG
    first_file = MY_CONFIG + ".1st"
    bak_file = MY_CONFIG + ".bak"
    result = None
    try:
        with open(MY_CONFIG, 'r') as stream:
            PUBLISH_CONFIG = json.load(stream)
        result = True
    except json.decoder.JSONDecodeError:
        if not os.path.isfile(first_file):
            if os.path.isfile(bak_file):
                shutil.move(bak_file, first_file)
            else:
                bak_file = first_file
        echo0('Loading "%s" failed. Moving to "%s"'
              % (MY_CONFIG, bak_file))
        if os.path.isfile(bak_file):
            os.remove(bak_file)
        shutil.move(MY_CONFIG, bak_file)
        result = False
        PUBLISH_CONFIG = {}
    if 'morescribus' not in PUBLISH_CONFIG:
        PUBLISH_CONFIG['morescribus'] = copy.deepcopy(
            DEFAULT_PUBLISH_CONFIG['morescribus']
        )
        return False
    else:
        for key, value in DEFAULT_PUBLISH_CONFIG['morescribus'].items():
            if key not in PUBLISH_CONFIG['morescribus']:
                PUBLISH_CONFIG['morescribus'][key] = value
    return result


def get_morescribus_setting(key):
    morescribus_d = PUBLISH_CONFIG.get('morescribus')
    value = None
    # if morescribus_d is None:
    #     PUBLISH_CONFIG['morescribus'] = {}
    #     morescribus_d = PUBLISH_CONFIG['morescribus']
    if morescribus_d:
        value = morescribus_d.get(key)
    if not value:
        echo0('[get_morescribus_setting] Warning:'
              ' no {"morescribus": {"%s": ...} } in "%s"'
              % (key, MY_CONFIG))
    return value


def set_morescribus_setting(key, value):
    morescribus_d = PUBLISH_CONFIG.get('morescribus')
    if morescribus_d is None:
        echo0('[set_morescribus_setting] Warning:'
              ' no {"morescribus": { "%s": ... } } in section "%s"'
              % (key, MY_CONFIG))
        PUBLISH_CONFIG['morescribus'] = {}
        morescribus_d = PUBLISH_CONFIG['morescribus']
    morescribus_d[key] = value


if os.path.isfile(MY_CONFIG):
    load_config()
else:
    PUBLISH_CONFIG = copy.deepcopy(DEFAULT_PUBLISH_CONFIG)
    # save_config()
    # echo0('There was no "%s", so it was saved with blank defaults.'
    #       % (MY_CONFIG))


def init_formats():
    """Set destination keys in EXPORT_FORMATS"""
    sla_path = get_morescribus_setting('scribus-project')
    if not sla_path:
        save_config()  # Save so user has something to edit.
        #  (load_config should already have overlaid defaults)
        return False
    # now = datetime.now()

    snapshots_dir = get_morescribus_setting("snapshots_dir")
    if snapshots_dir is None:
        echo0("Reverting to current directory.")
        snapshots_dir = ""

    m_time = os.path.getmtime(sla_path)
    in_dt = datetime.fromtimestamp(m_time)
    date_str = in_dt.strftime("%Y-%m-%d")

    for _, fmt in EXPORT_FORMATS.items():
        name = ("The_Path_of_Resistance-{}-{}dpi"
                .format(date_str, fmt['resolution']))
        if fmt.get('first') is not None:
            name += "-inner{}-{}".format(fmt['first'], fmt['last'])
        if fmt.get('section_3_start') is not None:
            name += "-prologue=page{}".format(fmt.get('section_3_start'))
        name += ".pdf"
        fmt['destination'] = os.path.join(snapshots_dir, name)
    return True


init_formats()


def export_pdf(options):
    if not init_formats():
        error = ('Configure booktacular with export_all or edit\n"%s".'
                 ' Example:\n%s'
                 % (MY_CONFIG, json.dumps(DEFAULT_PUBLISH_CONFIG)))
        if running_in_scribus:
            scribus.messageBox('Export Error', error, scribus.ICON_WARNING,
                               scribus.BUTTON_OK)
        else:
            echo0("Export Error: %s" % error)
        return False
    pdf = scribus.PDFfile()
    pdf.bookmarks = False  # True only for digital version
    # TODO: extrasGenerateTableOfContents
    # ^ Menu item defined in https://github.com/scribusproject/scribus/
    #   blob/f800e8dd44b69e6a01244063bc8e1b33a9000c5d/scribus/actionmanager.cpp
    # See:
    # cd ~/Downloads/git/scribusproject/scribus/scribus/plugins/scriptplugin/
    # grep "generate" -r | grep contents
    # Found: build_toc(tocList) but it doesn't seem to be well-supported
    #   in the API

    pdf.compress = options['compress']
    pdf.compressmtd = options['compressmtd']
    # ^ Compression method.  0:Automatic  1:JPEG  2:zip  3:None.
    pdf.quality = options['quality']

    pdf.resolution = options['resolution']
    pdf.downsample = options['downsample']
    if options.get('first'):
        first_page_n = options['first']
        last_page_n = options['last']
        pdf.pages = list(range(first_page_n, last_page_n+1))
    pdf.version = options['version']
    pdf.file = options['destination']
    pdf.version = options['version']
    pdf.useDocBleeds = options['useDocBleeds']
    pdf.fontEmbedding = options['fontEmbedding']
    print('[{} export_pdf] saving "{}"'.format(my_pretty_name, pdf.file))
    pdf.save()
    return True


# ^ API documentation definitions:
#   <https://github.com/scribusproject/scribus/blob/
#   34e45f567643b813b323e2f3248d19718293d68b/scribus/plugins/scriptplugin/
#   objpdffile.cpp>
# TODO: Change page numbering to: Sections, 3. Main, Start=21
# TODO: Find a way to get C "API documentation definitions" within an IDE ^
#    (Make a .pyi file?)


def main_cli():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "scribus-project",
        help="The document to prepare for publishing.",
    )
    parser.add_argument(
        "--release-dir",
        help="Directory for saving publishable snapshots (dated releases).",
    )
    args = parser.parse_args()
    if args.scribus_project:
        set_morescribus_setting("scribus-project", args.scribus_project)
        # formerly SLA_PATH
    if args.output_dir:
        set_morescribus_setting("release-dir", args.output_dir)
        # formerly SNAPSHOTS_PATH
    save_config()


if running_in_scribus:
    sla_path = get_morescribus_setting('scribus-project')
    if not os.path.isfile(sla_path):
        scribus.messageBox(
            'Export Error',
            ('Set {"morescribus": {"scribus-project": ...} } in "%s" first.'
             % (MY_CONFIG)),
            scribus.ICON_ERROR,
            scribus.BUTTON_OK,
        )
    print('[{}] opening "{}"'
          ''.format(my_pretty_name, sla_path))
    scribus.openDoc(sla_path)
    # scribus.setText('SomeField', 'some value')

    # TODO: ? Change page numbering to: Sections, 3. Main, Start=1
    # ^ NO, don't bother. Keep page numbering the same in print and digital.

    for _, options in EXPORT_FORMATS.items():
        export_pdf(options)
elif __name__ == "__main__":
    sys.exit(main_cli())
# else allow the module to be imported for other use (such as setting
#   options to prepare for buildpdf to run this as a Scribus arg, which
#   enables running_in_scribus)
