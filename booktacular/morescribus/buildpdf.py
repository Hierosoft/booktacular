#!/usr/bin/env python
'''
Produce a release.
- Run export_all.py in Scribus and check the result.
- Export the cover (page 1) using pdftoppm.

This script runs scribus_scripts/export_all.py (The path is determined
by: import scribus_scripts; scribus_scripts.export_all.__file__). That
file does most of the work, such as changing the PDF format. The 96dpi
file can be PDF/X-4 to support transparency since it is only for the
digital version, but the 600dpi file exported by it is a non-compliant
PDF/X-1a file with live transparency (See doc/preflight.md for more
information about compliance)

Options:
--force          Overwrite instead of skipping existing PDFs dated
                 today.
--no-preflight    Skip LONG preflight (pstill) operation.
'''
from __future__ import print_function
from __future__ import division
import sys
import os
import platform
import shlex
import subprocess
from datetime import (
    datetime,
    timedelta,
)

import scribus_scripts
from scribus_scripts.export_all import (
    echo0,
    # now,
    # date_str,
    SLA_PATH,
    # SNAPSHOTS_PATH,
    EXPORT_FORMATS,
    # REPO_DIR,
)

PREFLIGHT_MSG = '''
Preflight conversion is not implemented. It may be necessary to add PFA
and PFB fonts to
~/.local/lib/pstill
# ^ recommended by publisher support
then re-run cd ~/.local/lib/pstill && ./linkAllFonts.sh
before this script can be completed.
See also ~/Nextcloud/Tabletop/Pathfinder/projects/combine-pages.sh
on Poikilos' dev machine.

# The following section should match combine-pages.sh:

# My options:
# -v: verbose (helped diagnose "Base font 'Courier' missing,
#           turn on option -v for details"
# -H: help
# -d: dpi "interpreter dpi accuracy" or
#     -d placement_accuracy/raster_image_dpi/bw_image_dpi
# -c        turns on flate compression (PDF 1.2 feature)
#           when used as '-c -c' also turns on binary output
#           when used as '-c -c -c -c' also max. out the compression level
# -P  Convert all fonts to paths.
# -I        install PSFonts, initialize PStills font metrics & widths cache
# -m structured        "structured" output mode, no PDF processing
# -m XPDFACompat=#     set PDF/A-1b compat level (# = 7 - 9 for AA vers)
# -m XPDFX=INTENTNAME  turn on PDF/X output (default is PDF/X-3)
# -m XPDFXVERSION=1A   turn on PDF/X output Version 1a (needs XPDFX)
# -m XICCProfile=file  embed also this ICC color profile (needs XPDFX/A)
# -m Xoverprint         turn on overprinting takeover into result
# -C        set the output color model to RGB (default is CMYK)
# -J #      set JPEG compression for output, # quality is 0..100 [best]
#           when defined as "#,p" output will be progressive JPEG
# -W        turn on embedding of fonts by recollecting and generating
# -N path   tell PStill where to find TTF master fonts (automatic on Win32)
# -k        Allow the interpreter to write to files (Warning: security risk!)
# -S #      set logical start page number for PDF page numbering
# -f        allow empty pages in PDF (Default is empty pages are stripped)
# -Y        write calibrated colors (needs also option -C)
# -M defaultall         default plus font regeneration and transparency
#                       flattener [sic]
#    (-M has many other subcommands)
# transmode (flatten) options:
# -M default  # same as -2 -c -c -c -c -g -i -t -w 2000 -h 2000
# -M transmode=1  # full page
# -M transmode=2  # selective flatten
# -M transmode=3  # always

# More (See <https://www.wizards.de/~frank/PStillGuide_190.pdf>
#  or ~/.local/lib/pstill/pstill64 -H):
# -M transdpi=density_in_dpi
# -M transoptions=antialias
# -2 postscript level 2 compatibility. This is not recommended
#    "Any applications and tools that can only process PostScript Level
#    1or Level 2 should now be regarded as obsolete and upgraded, since
#    it is extremely unlikely that they can be configured to render
#    files reliably in conformance with PDF/X." according to
#    <thoughtco.com/difference-adobe-postscript-levels-1074580>.
'''

PREFLIGHT_MSG_EXAMPLE = """
usually:
#PSTILL=~/.local/lib/pstill/pstill64  # on Poikilos' PC
PSTILL=pstill
$PSTILL -o ~/Tabletop/ThePathOfResistance-more/snapshots/The_Path_of_Resistance-2023-07-26-300dpi-inner3-167-PDF_X-1a.pdf \
    -v -d 300/300/300 -c -c -c -c -m XPDFXVERSION=1A -m Xoverprint \
    -M transmode=2 -C -J 100 -W -f -N /home/owner/.local/share/fonts \
    /home/owner/Tabletop/ThePathOfResistance-more/snapshots/The_Path_of_Resistance-2023-07-26-300dpi-inner3-167.pdf
"""

print("sys.version_info: {}".format(sys.version_info))
HOME = None
if platform.system() == "Windows":
    HOME = os.environ['USERPROFILE']
else:
    HOME = os.environ['HOME']

SRC_WEB_COVER_FILE = os.path.join(HOME, "Tabletop",
                                  "ThePathOfResistance-more", "projects",
                                  "cover", "cover-2.0-web.jpg")


def which(name):
    """Find a program.

    An extension is automatically appended if on Windows and if name
    does not already include an extension.
    """
    # See also:
    # import distutils.spawn
    # distutils.spawn.find_executable("notepad.exe")
    # or Python 3.3+: shutil.which()
    PATH = os.environ['PATH']
    paths = PATH.split(os.pathsep)
    paths.insert(0, os.getcwd())
    paths.insert(0, os.path.dirname(os.path.realpath(__file__)))
    suffixes = [""]
    no_ext, dot_ext = os.path.splitext(name)
    if platform.system() == "Windows" and dot_ext == "":
        suffixes = [".exe", ".bat", ".com", ".py"]
    for suffix in suffixes:
        filename = name + suffix
        for parent in paths:
            subPath = os.path.join(parent, filename)
            if os.path.isfile(subPath):
                if not os.access(subPath, os.X_OK):
                    echo0("Skipping non-executable %s" % subPath)
                    continue
                return subPath
    return None


PSTILL_DIR = os.path.join(HOME, ".local", "lib", "pstill")
PSTILL_PATH = os.path.join(PSTILL_DIR, "pstill64")
SCRIBUS_PATH = which("scribus")
if SCRIBUS_PATH is None:
    raise FileNotFoundError(
        "scribus was not found in PATH nor current nor script directory"
    )
PDFTOPPM_PATH = which("pdftoppm")
if SCRIBUS_PATH is None:
    raise FileNotFoundError(
        "pdftoppm was not found in PATH nor current nor script directory"
    )
# EXPORT_SCRIPT = os.path.join(REPO_DIR, "export_all.py")
EXPORT_SCRIPT = scribus_scripts.export_all.__file__

PSTILL_MISSING_MSG = '''
# You are missing ~/.local/lib/pstill/pstill64. First do:
# Download pstill from pstill.com.
tar xf pstill*.tar.gz
# ^ such as pstill19008-5_i686_x64_linux.tar.gz
mv pstill_dist_x64 pstill
mkdir -p ~/.local/lib/
mv pstill ~/.local/lib/
cd ~/.local/lib/pstill
ln -s pstill64 pstill
# ^ required by ./linkAllFonts.sh
./linkAllFonts.sh
'''
# ^ Example output:
'''
FontManager: 0 fonts removed due to errors

* The following fonts are now installed & ready for use:
  1: PStillWDPattern

Done - PStill just displayed a list of installed fonts you can use
You may want to add additional fonts to PSFonts, just copy font files
of PFA or PFB type to the PSFonts directory, then run 'pstill -v -I'
again in the pstill base directory: ~/.local/lib/pstill
'''


def preflight_fix(src, dst, dpi="300", more_mode_options=None):
    '''Convert a PDF to PDF/X-1a format for publishers
    (flatten transparent files that are only compatible only with
    PDF/X-4 or later, etc).

    See PREFLIGHT_MSG for documentation, including of arguments
    provided to pstill.

    Args:
        src (string): A path or list of paths of PDFs to process.
        dst (string): The destination PDF path to write or overwrite that will
            be the new file that will include any preflight changes.
        dpi (Optional[int]): If "{dpi}dpi" is already  baked into the name of
            your file, make sure that you specify the *same* dpi here. The
            dpi will not affect the dst filename (dst is always used
            *as-is*).
        more_mode_options (Optional[list[str]]): Set the additional arguments
            for pstill. Defaults to ["-m", "XPDFXVERSION=1A", "-M",
            "getPageBBox", "-M", "transmode=2"]
    '''
    ICC = os.path.join(PSTILL_DIR, "profiles", "CGATS21_CRPC1.icc")
    # ^ I had added the CGATS21_CRPC1.icc file to the directory from
    #   <https://onebookshelfpublisherservice.zendesk.com/hc/en-us/articles/
    #   360022104293-Quick-Specifications-for-Print-Books>.
    commercial_print_options = [
        # -M default:
        #   -2 -c -c -c -c -g -i -t -w 2000 -h 2000
        #   -w and -h: set page dimensions in pts (1/72 in)
        "-M", "defaultall",  # recommended by pstill author
        # ^ default plus font regeneration and transparency flattener
        # ^ ok since even works with -P (-P invalidates -i -t) conv. to paths
        # "-M", "pdfpagerange=1,10",
        # "-P",  # outline all fonts! "turn all text to paths...font'less"
        # ^ Author says -P isn't necessary with "-M noProxyText" since
        #   excluding proxy text (which is for extractable text) should
        #   prevent the missing Times-Roman error on DriveThruRPG
        # -d (generated from dpi below)
        "-M", "noProxyText",  # turn off extractable text (prevents missing
        #   Times-Roman error ok since non-pstill version)
        # TODO: ^ See if new options work with Barnes&Noble, otherwise add -P
        "-M", "keepPDFBoxes",
        "-m", "XPDFX=CGATS.21-2",  # "intent" of your specific ICC profile
        # ^ The pstill author says
        #   <https://www.color.org/registry/CGATS21_CRPC1.xalter> lists this
        #   string as the "printing condition" for CGATS21_CRPC1.icc.
        #
        "-m", "XPDFXVERSION=1A",
        # "-m", "XPDFX=US Web Coated (SWOP) v2",  # rec. by pstill author
        # Both options below are necessary as explained by pstill author:
        "-m", "XICCProfile={}".format(ICC),  # only does embedding *not* conv.
        "-M", "cmykprofile={}".format(ICC),  # only does *sRGB conv* not embed
        # "-M", "getPageBBox",
        # "-g",  # "turns on get page size from job (if any)
        #   ...Use together with -M getPageBBox to prefer the
        #   PageBoundingBox"
        # ^ pstill author says -M keepPDFBoxes keeps original & invalidates -g
        "-M", "transmode=2",
    ]
    if more_mode_options is None:
        more_mode_options = commercial_print_options
    prefix = "[release.py preflight_fix] "
    sources = [src]
    if isinstance(src, list):
        sources = src

    if not os.path.isfile(PSTILL_PATH):
        echo0(PSTILL_MISSING_MSG)
        return 1
    fonts_path = os.path.join(HOME, ".local", "share", "fonts")
    # TODO: See if installing mscorefonts from sourceforge
    #   (See <https://www.fosslinux.com/42406/
    #   how-to-install-microsoft-truetype-fonts-on-fedora.htm>)
    #   fixes error in DriveThruRPG upload. I also did:
    #   cp /usr/share/fonts/dejavu-serif-fonts/DejaVuSerif.ttf \
    #     ~/.local/share/fonts/Times-Roman.ttf

    # See PREFLIGHT_MSG above for comments on each option used.
    # The following should match
    #   ~/Nextcloud/Tabletop/Pathfinder/projects/combine-pages.sh:
    # no_ext, dot_ext = os.path.splitext(src)
    cmd_parts_old = [
        PSTILL_PATH,
        "-o", dst,
        "-v",
        "-d", "{dpi}/{dpi}/{dpi}".format(dpi=dpi),
        "-c", "-c", "-c", "-c",  # max compression
        # "-i",  # enable including non-standard fonts in output
        # "-t",  # turns on mapping of PS transfer function to output
        *more_mode_options,
        # print version: -m XPDFXVERSION=1A -M transmode=2
        # formerly used -m Xoverprint but it's ink separation not bleed!
        "-C",  # Set color to RGB (default is CMYK)
        "-J", "100",
        # "-W",  # embed fonts by recollecting & generating
        # ^ -W is not correct for print! For PDF X/1-a, outline instead.
        #   With or without -W, DriveThruRPG still says, "The following
        #   fonts are not embedded: Times-Roman, Times-Roman."
        #   (Adding -g, -i, -t didn't help) -W -W is "mode 2" but
        #   not explained in -H nor documentation...
        "-P",  # outline all fonts! "turn all text to paths...font'less"
        "-f",  # allow empty pages
        "-N", fonts_path,
        *sources
    ]
    # via pstill author via e-mail 2023-08-31:
    #   -M defaultall -o PDF_X-1a.pdf -v -d 300/300/300  -m
    #   XPDFX=INTENTNAME -m XPDFXVERSION=1A -J 100 -P -f -N
    #   ~/.local/share/fonts inner3-167.pdf
    cmd_parts = [ # via pstill author e-mail 20230831, except:
        # - he says try remove -P
        # - I added getPageBBox from my old command to more_mode_options
        # - I fixed -M transmode=2 adding missing space before -M
        #   in more_mode_options (wasn't being used since wrong)
        PSTILL_PATH,
        # "-M", "defaultall",  # added to more_mode_options
        "-o", dst,
        "-v",
        "-d", "{dpi}/{dpi}/{dpi}".format(dpi=dpi),
        # "-m", 'XPDFX=US Web Coated (SWOP) v2',# added to more_mode_options
        *more_mode_options,  # -M defaultall
        # "-m", 'XPDFXVERSION=1A', already in *more_mode_options
        "-J", "100",
        "-f",
        "-N", fonts_path,
        *sources
    ]

    cmd = shlex.join(cmd_parts)
    run_start_dt = datetime.now()
    mins = 4 * 60 + 35  # the usual # of mins it takes
    spkb = float(mins * 60) / float(245738679 / 1024)  # seconds per kb
    # ^ Based on 2023-07-26 print release: /(245738679/1024)
    # TODO: Get the collective size of the images as well.
    kb = os.stat(src).st_size / 1024
    est_seconds = kb * spkb
    est_delta = timedelta(seconds=est_seconds)
    eta = run_start_dt + est_delta
    import re
    matches = list(re.finditer("-M", cmd))
    # NOTE findall only gets the text, not match objects!
    if matches:
        for match in matches:
            start = match.span()[0]
            if cmd[start - 1:start] != " ":
                # If there is no space before the switch
                #   (Prevent regression)
                raise NotImplementedError(
                    "There is no space before -M in command: `{}`"
                    "  # parts: {}".format(cmd, cmd_parts)
                )
    LOG_DT_FMT = "%Y-%m-%d %H:%M"
    LOG_DT_START_STR = run_start_dt.strftime(LOG_DT_FMT)
    echo0('\n\n' + prefix + 'running `{}` at {} (eta {})...'
          ''.format(cmd, LOG_DT_START_STR,
                    eta.strftime("%H:%M")))

    # out = subprocess.check_output(
    #     cmd_parts,
    #     stderr=subprocess.STDOUT,  # capture stderr too.
    # )
    proc = subprocess.Popen(cmd_parts, stdout=subprocess.PIPE, bufsize=1)

    # lines = out.split(b'\n')
    dst_dir, dst_name = os.path.split(os.path.realpath(dst))
    dst_no_ext, _ = os.path.splitext(dst_name)
    log_name = "converted-{}.log".format(dst_no_ext)
    log_path = os.path.join(dst_dir, log_name)
    log_mode = "wb"
    echo0(prefix + 'showing output (and saving to "{}")'.format(log_path))

    def to_bytes(value):
        if not isinstance(value, bytes):
            return str(value).encode("utf-8")
        return value

    def to_str(value):
        if not isinstance(value, str):
            return value.decode("utf-8")
        return value

    if "b" in log_mode:
        conv = to_bytes
    else:
        conv = to_str

    with open(log_path, log_mode) as stream:
        def both0(*args, **kwargs):
            """Write args (but *not* newline, since buffer size is arbitrary)
            """
            args = list(args)
            for i in range(len(args)):
                args[i] = conv(args[i])
                stream.write(args[i])
                if (i > 0) and (not args[i - 1].endswith(conv(" "))):
                    stream.write(conv(" "))
            for i in range(len(args)):
                args[i] = to_str(args[i])
            sys.stderr.write(*args, **kwargs)
            sys.stderr.flush()
            stream.flush()

        both0(prefix + "started {}\n".format(LOG_DT_START_STR))
        while True:  # for rawL in lines:
            # "for line in p.stdout" buffers aggressively according to
            #   <https://stackoverflow.com/a/803421/4541104>
            rawL = proc.stdout.readline()
            if not rawL:
                break
            both0(rawL)
        proc.stdout.close()
        proc.wait()

        run_end_dt = datetime.now()
        LOG_DT_END_STR = run_end_dt.strftime(LOG_DT_FMT)
        both0(prefix + "done {}\n".format(LOG_DT_END_STR))

        preflight_delta = run_end_dt - run_start_dt
        minutes = preflight_delta.seconds // 60
        seconds = preflight_delta.seconds - (minutes * 60)
        both0(prefix + "done in {}m{}s\n".format(minutes, seconds))

    echo0(prefix + 'saved "{}"'.format(log_path))

    if not os.path.isfile(dst):
        echo0(prefix + 'Error: `{}` did not produce "{}"'
              ''.format(cmd, dst))
        return 1
    else:
        echo0(prefix + 'Created "{}"'.format(dst))
    echo0("Check the result by comparing the output of the two commands:")
    echo0('    pdfinfo -box "{}"'.format(src))
    echo0('    pdfinfo -box "{}"'.format(dst))
    echo0("\n")
    return 0


def export_web_and_ad_cover_images(path, dst_path, page=1):
    '''
    Args:
        dst_path (str): -###.jpg (where ### is page number such as 001)
            will be added to this path for each page. The extension will
            be removed.
    '''
    # Version without words (*only* for ads)
    # DO NOT do (separate version for ads doesn't have the title on it):
    # echo0('Copying "{}"'.format(SRC_WEB_COVER_FILE))
    # dst_cover = os.path.join(HOME, "Nextcloud", "www", "zahyest.com",
    #                          "imgsite", "cover-book_1.jpg")
    # shutil.copy(SRC_WEB_COVER_FILE, dst_cover)  # TODO: only if newer
    # echo0('* Updated "{}"'.format(dst_cover))  # TODO: only echo if changed
    # Version with words (for website & store(s) thumbnail)
    dpi = 100
    dst_dir = os.path.dirname(dst_path)
    dst_path_no_ext, dot_ext = os.path.splitext(dst_path)
    if dot_ext.lower() != ".jpg":
        raise ValueError("The destination must be jpg.")
    # tmp_name = "cover"  # has a tmp name since 1 will get added anyway,
    # so it must be renamed anyway.
    cmd_parts = [PDFTOPPM_PATH, path, "-f", str(page), "-l", str(page),
                 "-jpeg", "-jpegopt", "quality=97,progressive=y,optimize=y",
                 "-r", str(dpi), dst_path]
    echo0("[release.py export_web_and_ad_cover_images] Running `{}`..."
          "".format(shlex.join(cmd_parts)))

    # try
    out = subprocess.check_output(
        cmd_parts,
        stderr=subprocess.STDOUT,  # capture stderr too.
    )
    # ^ just processes arguments and does the call below :(
    '''
    out = subprocess.run(
        cmd_parts,
        stdout=PIPE,
        # timeout=timeout,
        # check=True,
        **kwargs
    ).stdout
    '''
    # ^ raises subprocess.CalledProcessError on failure if check=True
    # TODO: Try getting proc output in exception, using ex.output

    # expected_name = tmp_name + str(page) + ".jpg"
    # expected_path = os.path.join(dst_dir, expected_name)
    expected_path = dst_path + "-" + str(page).rjust(3, '0') + ".jpg"
    if not os.path.isfile(expected_path):
        raise RuntimeError(
            '`{}` did not produce "{}"'
            ''.format(shlex.join(cmd_parts), expected_path)
        )
    # -f: first page
    # -l: first page
    # ^ See <https://www.mankier.com/1/pdftoppm>
    echo0('[export_web_and_ad_cover_images] Created "{}"'
          .format(expected_path))
    '''
    if os.path.isfile(path):
        raise NotImplementedError('"{}" already exists.'.format(path))
    shutil.move(expected_path, path)

    # TODO: only push to web if changed

    '''
    echo0("Manual steps are necessary:")
    echo0('cp "{}" "{}"'.format(expected_path, dst_path))
    echo0("cd ~/Nextcloud/www/zahyest.com && push-pages --images")
    return 0


def export_pdfs(options={}):
    '''Export each PDF variant using the export_all script.

    Feed the export_all script to scribus. The script uses
    EXPORT_FORMATS for the format options, but this function only uses
    the dictionary for the filename, date, and preflight_fix dpi.

    Print version:
    - Outline all fonts (NOTE: Required for print, but don't use for
      digital since prevents full text search)
    - PDF/X-1 (collapse transparency before uploading)
    - Use Document Bleeds
    '''
    prefix = "[export_pdfs] "
    cmd_parts = [SCRIBUS_PATH, "-ns", "-g", "--python-script", EXPORT_SCRIPT]
    '''
    -g: "No GUI. Scribus wont display any dialogs or windows and will
        exit once the script is ended. This prevent dialogs to interrupt
        the script."
    -ns:

    More (See <https://wiki.scribus.net/canvas/Command_line_scripts>):
    scribus -g -py export_to_pdf.py -version 13 -bleedr 2
        -compress 1 -info 'test title' -file 'test.pdf' -- testdoc.sla

    -bleedr <rightbleedsize>
    -info <infostring>
    -pages <listofpage> : receives the desired list of pages.
        Defaults to [1] : first page.
        (not necessary--see pdf.pages=[1] in step1.scribus.py)
    '''

    '''
    Digital version:
    - Embed fonts (allows full-text search!)
    - PDF/X-4 (supports transparency)
    - Bleeds don't matter
    '''
    error_count = 0
    missing_count = 0
    done_count = 0
    older_count = 0
    in_dt = os.path.getmtime(SLA_PATH)
    for _, fmt in EXPORT_FORMATS.items():
        fmt['old_dt'] = None
        if os.path.isfile(fmt['destination']):
            m_time = os.path.getmtime(fmt['destination'])
            fmt['old_dt'] = datetime.fromtimestamp(m_time)
            done_count += 1
            if m_time < in_dt:
                older_count += 1
                echo0(prefix + 'removing "{}" older than "{}"'
                      ''.format(fmt['destination'], SLA_PATH))
                os.remove(fmt['destination'])
            else:
                if m_time == in_dt:
                    echo0(prefix + 'keeping "{}" with date matching SLA'
                          ''.format(fmt['destination']))
                else:
                    echo0(prefix + 'WARNING: keeping "{}"'
                          ' with date newer than SLA'
                          ''.format(fmt['destination']))
                continue
        missing_count += 1
    if (missing_count + older_count) < 1:
        if options.get('force') is True:
            echo0(prefix
                  + "[export_pdfs] Overwriting anyway due to 'force' option.")
    if ((missing_count + older_count) > 0) or (options.get('force') is True):
        print("\n\nPlease wait for Scribus to finish and close automatically!")
        print('[release.py main] Waiting for `{}` to complete'
              ' (This may take a while)...'
              ''.format(shlex.join(cmd_parts)))
        subprocess.check_output(
            cmd_parts,
            stderr=subprocess.STDOUT,  # capture stderr too.
        )
        for _, fmt in EXPORT_FORMATS.items():
            if not os.path.isfile(fmt['destination']):
                error_count += 1
                echo0(prefix + 'Error: `{} {} ...` did not produce "{}"'
                      .format(SCRIBUS_PATH, EXPORT_SCRIPT, fmt['destination']))
            elif fmt.get('old_dt') is not None:
                m_time = os.path.getmtime(fmt['destination'])
                if fmt['old_dt'] >= datetime.fromtimestamp(m_time):
                    error_count += 1
                    echo0(prefix + 'Error: `{} {} ...`'
                          ' did update the existing "{}"'
                          ' according to the modification time.'
                          ''.format(SCRIBUS_PATH, EXPORT_SCRIPT,
                                    fmt['destination']))
        code = 1
    echo0("\n" + prefix + "Running pre-flight operations...")
    ex_path = EXPORT_FORMATS['print']['destination']
    # TODO: Check bleeds with ['pdfinfo', '-box', ex_path]
    no_ext, dot_ext = os.path.splitext(ex_path)

    if options.get('preflight'):
        code = preflight_fix(
            ex_path,
            no_ext + "-PDF_X-1a" + dot_ext,
            dpi=EXPORT_FORMATS['print']['resolution']
        )
    if code != 0:
        error_count += 1

    if error_count > 1:
        return error_count
    return 0


def main():
    code = 0
    missing_count = 0
    done_count = 0
    check_paths = []
    options = {
        'preflight': True,
    }
    exist_action = "skipping"
    for arg_i in range(1, len(sys.argv)):
        # ^ 1 to skip 0 (this script)
        arg = sys.argv[arg_i]
        if arg == "--force":
            options['force'] = True
            exist_action = "overwriting"
        elif arg == "--no-preflight":
            options['preflight'] = False
    for fmt in EXPORT_FORMATS.keys():
        # Check if it was already done today.
        ex_path = EXPORT_FORMATS[fmt]['destination']
        if os.path.isfile(ex_path):
            echo0('* {} existing "{}"'.format(exist_action, ex_path))
            done_count += 1
            continue
        else:
            echo0('* "{}" is planned to be created.'.format(ex_path))
            check_paths.append(ex_path)
        missing_count += 1
    # if (missing_count > 0) or (options.get('force') is True):
    code = export_pdfs(options=options)
    if code != 0:
        return code
    # else:
    #     echo0("There are no new PDFs to create.")
    #     code = 0
    # TODO: check if files were made (didn't exist or older *before* command)
    WEB_COVER_PATH = os.path.join(HOME, "Nextcloud", "www", "zahyest.com",
                                  "imgsite", "cover-book_1.jpg")
    if not os.path.isfile(EXPORT_FORMATS['digital']['destination']):
        echo0('Error: "{}" cannot be created without "{}"'
              ''.format(WEB_COVER_PATH,
                        EXPORT_FORMATS['digital']['destination']))
        return 1

    code = export_web_and_ad_cover_images(
        EXPORT_FORMATS['digital']['destination'],
        WEB_COVER_PATH
    )
    if code != 0:
        return code

    for ex_path in check_paths:
        # ^ EXPORT_FORMATS['digital']['destination'] was already checked
        #   above in case it worked and the other didn't and
        #   WEB_COVER_PATH could still be created, but now return an
        #   error code if *any* is missing.
        if not os.path.isfile(ex_path):
            echo0('Error: There is no "{}"'
                  ''.format(ex_path))
            code = 1

    return code


if __name__ == "__main__":
    sys.exit(main())
