# -*- coding: utf-8 -*-
## does summation of echoes using external python script
import sys
import os
import os.path
import subprocess


import argparse
descriptProg = """
Reverse UDEFT FID for easy processing of refocused echo. 
The FID is time reversed then imaginary points are negated to 
keep the frequency axis correct.
Processed data is stored in spectrum tab for further processing
in Topspin.
Only TDEFF points are stored back corresponding only to refocussed echo.
"""

parser = argparse.ArgumentParser(description=descriptProg)
parser.add_argument('--td', required=False, type=int, default=0,
                    help='actual FID td points')
args = parser.parse_args()

# installation directory is relative to current script location
DIRINST = os.path.dirname(sys.argv[0]) + "/../"
# where is the external python executable
CPYTHON = os.getenv('CPYTHON', "NotDefined")
if "python" not in CPYTHON:
		MSG("CPYTHON environment not defined")
		EXIT()
# MSG(CPYTHON)


dataset = CURDATA()
TDEFF = GETPAR("TDeff")
if not args.td:
    TD = GETPAR("TD")
else:
    TD = args.td 
# special treatment for topspin<3
def fullpath(dataset):
	dat = dataset[:]   # make a copy because I don't want to modify the original array
	if len(dat) == 5:    # for topspin 2-
	        dat[3] = "%s/data/%s/nmr" % (dat[3], dat[4])
	fulldata = "%s/%s/%s/pdata/%s/" % (dat[3], dat[0], dat[1], dat[2])
	return fulldata
fulldataPATH = fullpath(dataset)

opt_args = "--tdeff %s --td %s" % (TDEFF, TD)

script = os.path.expanduser(DIRINST + "/CpyBin/reverseUdeft_.py")
# os.system(" ".join((CPYTHON, script, opt_args, fulldataPATH)))
subprocess.call([CPYTHON] + [script] + opt_args.split() + [fulldataPATH])    

RE(dataset)
