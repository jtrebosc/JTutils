# -*- coding: utf-8 -*-
## does summation of echoes using external python script
import sys
import os
import os.path
import subprocess
import JTutils


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

dataset = CURDATA()
TDEFF = GETPAR("TDeff")
if not args.td:
    TD = GETPAR("TD")
else:
    TD = args.td 
fulldataPATH = JTutils.fullpath(dataset)

opt_args = ""
"--tdeff %s --td %s " % (TDEFF, TD)

JTutils.run_CpyBin_script('reverseUdeft_.py', opt_args.split()+[fulldataPATH])

RE(dataset)
