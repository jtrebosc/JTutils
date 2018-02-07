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
parser.add_argument('--tdeff', required=True, type=int,
                    help='only keep tdeff points')
parser.add_argument('infile', help='Full path of the dataset to process')
args = parser.parse_args()


data = bruker.splitprocpath(args.infile)

#initialize dataset
dat = bruker.dataset(data)

#read 1D fid file and remove digital filter
spect = dat.readfidc()
digfilt = int(np.round(dat.getdigfilt()))

if args.td:
    print "limit fid to " + str(args.td), digfilt
    td = args.td//2 - digfilt
    spect = spect[0:td]
print spect.shape, digfilt
tdeff = args.tdeff//2 - digfilt
# reverse time and conjugate FID and truncate to TDeff
spect = np.conj(spect[::-1])
if (spect.size > tdeff) and  (tdeff > 0):
    spect = spect[0:tdeff]
print spect.shape

# extend array to SI size
tdc = spect.size
si = int(dat.readprocpar("SI", status=False, dimension=1))
if (si < tdc):
    si = tdc
spect = np.concatenate((spect,np.zeros(si-tdc)))
print spect.shape
dat.writespect1dri(spect.real,spect.imag)

# The FID stored will be considered as inverse fourier transform
# in time domain 
# digital filter has been removed
dat.writeprocpar("PKNL", "yes", True)

# set all optionnal status processing parameters to 0 (default)
ProcOptions = {"WDW": ["LB", "GB", "SSB", "TM1", "TM2"],
               "PH_mod": ["PHC0", "PHC1"], "BC_mod": ["BCFW", "COROFFS"],
               "ME_mod": ["NCOEF", "LPBIN", "TDoff"], 
               "FT_mod": ["FTSIZE", "FCOR"]}
for dim in [1]:
    for par in ProcOptions.keys():
        dat.writeprocpar(par, "0", True, dimension=dim)
        for opt in ProcOptions[par]:
            dat.writeprocpar(opt, "0", True, dimension=dim)

# adjust FT parameters
dat.writeprocpar("FT_mod", "2", True, dimension=1)  # FT_mod set to ift
dat.writeprocpar("FTSIZE", str(si), True, dimension=1)
dat.writeprocpar("FCOR", "0", True, dimension=1)

# adjust processing spectral window
swh = float(dat.readacqpar("SW_h", status=True, dimension=1))
dat.writeprocpar("SW_p", str(swh), True, dimension=1)

