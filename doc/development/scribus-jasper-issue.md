- [ ] report this issue
Scribus has the following output on running a script:
```
WARNING: YOUR CODE IS RELYING ON DEPRECATED FUNCTIONALITY IN THE JASPER
LIBRARY.  THIS FUNCTIONALITY WILL BE REMOVED IN THE NEAR FUTURE. PLEASE
FIX THIS PROBLEM BEFORE YOUR CODE STOPS WORKING.
deprecation warning: use of jas_init is deprecated
warning: The application program did not set the memory limit for the JasPer library.
warning: The JasPer memory limit is being defaulted to a value that may be inappropriate for the system.  If the default is too small, some reasonable encoding/decoding operations will fail.  If the default is too large, security vulnerabilities will result (e.g., decoding a malicious image could exhaust all memory and crash the system.
warning: setting JasPer memory limit to 25151481856 bytes
WARNING: YOUR CODE IS RELYING ON DEPRECATED FUNCTIONALITY IN THE JASPER
LIBRARY.  THIS FUNCTIONALITY WILL BE REMOVED IN THE NEAR FUTURE. PLEASE
FIX THIS PROBLEM BEFORE YOUR CODE STOPS WORKING.
deprecation warning: use of jas_cleanup is deprecated
pathForIcon: Unable to load icon /usr/share/scribus/icons/1_5_1/lab.png: File not found
pathForIcon: Unable to load icon /usr/share/scribus/icons/1_5_1/spot.png: File not found
pathForIcon: Unable to load icon /usr/share/scribus/icons/1_5_1/register.png: File not found
```
