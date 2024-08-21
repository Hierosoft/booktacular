'''
# See https://wiki.scribus.net/canvas/Command_line_scripts
Produce a PDF for the SLA passed as a parameter.
Use the same file name and replaces the .sla extension with .pdf

usage:
scribus -g -ns -py step1.scribus.py
'''

import os
import sys
from datetime import datetime
my_longname = "booktacular export_all.py"
'''
HOME = None
if platform.system() == "Windows":
    HOME = os.environ['USERPROFILE']
else:
    HOME = os.environ['HOME']
'''
# ^ platform is not defined, even if imported :(, so:
try:
    HOME = os.environ['USERPROFILE']
except KeyError:
    HOME = os.environ['HOME']


# if not scribus.haveDoc():
#     raise Exception("Error: No document.")
# name_noext = os.path.splitext(scribus.getDocName())[0]
# ^ only raise or open if a document file arg was expected to be sent to
#   scribus
def echo0(*args):
    print(*args, file=sys.stderr)


MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(MODULE_DIR)
SLA_PATH = os.path.join(REPO_DIR, 'The Path of Resistance.sla')
if sys.version_info.major < 3:
    ModuleNotFoundError = ImportError

SNAPSHOTS_PATH = os.path.join(HOME, "Tabletop", "ThePathOfResistance-more",
                              "snapshots")
# now = datetime.now()
m_time = os.path.getmtime(SLA_PATH)
in_dt = datetime.fromtimestamp(m_time)
date_str = in_dt.strftime("%Y-%m-%d")

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

for _, fmt in EXPORT_FORMATS.items():
    name = ("The_Path_of_Resistance-{}-{}dpi"
            .format(date_str, fmt['resolution']))
    if fmt.get('first') is not None:
        name += "-inner{}-{}".format(fmt['first'], fmt['last'])
    if fmt.get('section_3_start') is not None:
        name += "-prologue=page{}".format(fmt.get('section_3_start'))
    name += ".pdf"
    fmt['destination'] = os.path.join(SNAPSHOTS_PATH, name)

enable_scribus = False
try:
    import scribus  # type: ignore
    enable_scribus = True
    # In this case, it is running within Scribus.
except ModuleNotFoundError:
    echo0("INFO: {} is being imported as module since not running in Scribus."
          "".format(os.path.basename(os.path.realpath(__file__))))


def export_pdf(options):
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
    print('[{} export_pdf] saving "{}"'.format(my_longname, pdf.file))
    pdf.save()


# ^ API documentation definitions:
#   <https://github.com/scribusproject/scribus/blob/
#   34e45f567643b813b323e2f3248d19718293d68b/scribus/plugins/scriptplugin/
#   objpdffile.cpp>
# TODO: Change page numbering to: Sections, 3. Main, Start=21
# TODO: Find a way to get C "API documentation definitions" within an IDE ^

if enable_scribus:
    print('[{}] opening "{}"'
          ''.format(my_longname, SLA_PATH))
    scribus.openDoc(SLA_PATH)
    # scribus.setText('SomeField', 'some value')

    # TODO: ? Change page numbering to: Sections, 3. Main, Start=1
    # ^ NO, don't bother. Keep page numbering the same in print and digital.

    for _, options in EXPORT_FORMATS.items():
        export_pdf(options)
