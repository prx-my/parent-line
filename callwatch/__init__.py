import sys

if sys.version_info < (3, 11):
    sys.exit("Parent Line needs Python 3.11 or newer; this is Python %d.%d. Run python3 check.py for what to install." % sys.version_info[:2])
