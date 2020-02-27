#!/usr/bin/python
# -*- coding: utf-8 -*-
# copyright Julien TREBOSC 2017-2018
from __future__ import division
import sys
#sys.path.append('/opt/pulse_programs/CpyLib')
import bruker
import numpy.core as np


# arguments management
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
                    help='last FID point of refocused echo')
parser.add_argument('--tdeff', required=False, type=int,
                    help='only keep tdeff points', default=0)
parser.add_argument('infile', help='Full path of the dataset to process')
args = parser.parse_args()


data = bruker.splitprocpath(args.infile)

#initialize dataset
dat = bruker.dataset(data)

#read 1D fid file and remove digital filter
spect = dat.readfidc(rmGRPDLY=False)
digfilt = int(round(dat.getdigfilt()))
(td_spectrum,) = spect.shape

# calculate the theoretical td from pulse sequence parameters unless td is provided as argument
if args.td:
    print("limit fid to " + str(args.td), digfilt)
    td = args.td//2 - digfilt
else:
    "p13+3.5+d6*2+de*2+d3*2" # delays to consider
    p13 = float(dat.readacqpar("P 13"))
    d3 = float(dat.readacqpar("D 3"))*1e6
    d6 = float(dat.readacqpar("D 6"))*1e6
    de = float(dat.readacqpar("DE"))
    dw = 1e6/float(dat.readacqpar("SW_h"))
    td = int(round((p13+3.5+2*(d3+d6+de))/dw)+2*digfilt)
    #print("else ",td)
#print(td, td_spectrum)
# some times td is too short (final digital filter is truncated) and one must pad with 0
if td_spectrum < td:
    spect = bruker.pad(spect,(0,td-td_spectrum),mode='constant')
#print(spect.shape, digfilt)
else : # if too long then truncate FID to optimal td
    spect = spect[0:td]

# tdeff is read from proc file unless provided as argument
if args.tdeff:
    tdeff = args.tdeff//2 
else :
    tdeff = int(dat.readprocpar("TDeff", status=False))//2

# reverse time, conjugate FID 
spect = np.conj(spect[::-1])
#print(spect.shape)
# and truncate to TDeff
if (spect.size > tdeff) and  (tdeff > 0):
    spect = spect[0:tdeff]

# extend array to SI size (from proc file, this is zero filling)
(tdc,) = spect.shape
si = int(dat.readprocpar("SI", status=False, dimension=1))
if (si < tdc):
    tdc = si
    spect = spect[0:si]
spect = np.concatenate((spect,np.zeros(si-tdc)))
#print(spect.shape)
dat.writespect1dri(spect.real,spect.imag)

# The FID stored will be considered as unprocessed time domain
# digital filter has not been removed
dat.writeprocpar("PKNL", "yes", False)

# set all optionnal status processing parameters to 0 (default)
ProcOptions = {"WDW": ["LB", "GB", "SSB", "TM1", "TM2"],
               "PH_mod": ["PHC0", "PHC1"], "BC_mod": ["BCFW", "COROFFS"],
               "ME_mod": ["NCOEF", "LPBIN", "TDoff"], 
               "FT_mod": ["FTSIZE", "FCOR"]}
for dim in [1]:
    for par in ProcOptions:
        dat.writeprocpar(par, "0", True, dimension=dim)
        for opt in ProcOptions[par]:
            dat.writeprocpar(opt, "0", True, dimension=dim)

# adjust FT parameters
dat.writeprocpar("FT_mod", "0", True, dimension=1)  # FT_mod set to ift
dat.writeprocpar("FTSIZE", str(si), True, dimension=1)
dat.writeprocpar("FCOR", "0", True, dimension=1)

# adjust processing spectral window
swh = float(dat.readacqpar("SW_h", status=True, dimension=1))
dat.writeprocpar("SW_p", str(swh), True, dimension=1)

