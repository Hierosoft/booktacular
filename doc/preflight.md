# Preflight


release.py automates Scribus to generate 2 PDFs:
- 96dpi PDF/X-4 format
- 600dpi PDF/X-1a format (non-compliant)

...both described in sections below.

## 96dpi PDF/X-4 format
This is the first PDF format version to support live transparency. This
newer format works (only) for the digital copy on DriveThruRPG (as of
2023) including for the preview and quick preview features.

Options:
- outline all fonts: No (to allow full text searching)

## 600dpi PDF/X-1a format
This file is not entirely compliant due to transparency:
- The [pstill](#pstill) program was recommended by DriveThruRPG to ensure the format is correct.
  - ImageMagick may work but it converts *everything to one big raster for each page*.
  - ImageMagick's -flatten option does *not* do this--it combines all pages not just layers!
- However, B&N Press automatically converts the file to generate a proof, so that proof can be sent to DriveThruRPG if pstill is not used.
- outline all fonts: Yes (This is the only way B&N Press will accept the file as of 2022)

### pstill
- Website: <https://www.wizards.de/~frank/>
- Documentation: http://www.wizards.de/~frank/WP/

PStill (or Adobe Acrobat) can do preflight conversion according to a DriveThruRPG publisher support agent as of 2023.

#### Install
<https://github.com/Poikilos/nopackage> can automatically install the Linux binary gz to "$HOME/.local/lib/pstill".
- Add color profiles (such as CGATS21_CRPC1.icc used by DriveThruRPG) to ~/.local/lib/pstill/profiles
  - Color profiles should also be installed system-wide such as installing `gnome-color-manager` then double-clicking the icc file. It puts them in ~/.local/share/icc/ on Fedora 38.
    - [ ] TODO: find document where this is discussed further. Install a color profile installer to install the icc file.
  - The original document should use sRGB if the images were created that way! The conversion process is what conforms the colors that aren't conformed already, so unless every image is already conformed before putting it into Scribus, use sRGB as the Scribus format (though a different format can be used for export). Also, sending the file to the publisher in RGB only risks the colors being out of gamut (range). If you already account for that, their conversion process will just convert it right there and it will be approximately what you need if your images were designed with sRGB in mind and Scribus designates the format as such in Document Setup.
