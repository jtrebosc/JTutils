#!/usr/bin/python
# -*- coding: utf-8 -*-
# copyright Julien TREBOSC 2012-2013
# check that variable PYTHONPATH points to the right folder for bruker.py
#      library
from __future__ import division, print_function

import numpy
import sys
import bruker
import math


# gestion des arguments
import argparse
parser = argparse.ArgumentParser(
  description='apodize each echoes by gaussian broadening in a qcpmg experiment')
parser.add_argument('-g', '--gb', type=float, 
                    help='Gaussian broadening applied to each echo', default=0)
parser.add_argument('-c', type=float, help='qcpmg cycle in us')
parser.add_argument('-s', type=float, 
   help='echo position from start of FID (digital filter excluded) in us')
parser.add_argument('infile', help='Full path of the dataset to process')

args = parser.parse_args()
dat = bruker.dataset(bruker.splitprocpath(args.infile))

# read FID file (digital filter is removed by default)
serfile = dat.readfid()

# calculate duration of an echo in point unit
dw = 1e6/float(dat.readacqpar("SW_h"))
P60 = float(dat.readacqpar("P 60")) # should store the cycle time
# in case cycle tiume is not stored in P60, this program uses a default
# calculation based on D3, D6, P4, P3
D3 = float(dat.readacqpar("D 3"))*1e6
D6 = float(dat.readacqpar("D 6"))*1e6
P4 = float(dat.readacqpar("P 4"))
P3 = float(dat.readacqpar("P 3"))
# cycle is set to a
if args.c : # one can provide the cycle in argument
    cycle = float(args.c)
elif P60 > 0: # pulse program should store status cycle in P60
    cycle = P60
else : # default behavior may depend on pulse program implementation
    cycle = 2*(D3+D6+2)+P4

# get the number of echoes
n_echoes = int(dat.readacqpar("L 22")) + 1

ppc = cycle/dw
npoints = int(round(cycle/dw))

if ppc-npoints > 0.001:
    print("Warning echo cycle is not multiple of dwell")
    roundChunk = True
else:
    roundChunk = False

# verifie si TD est coherent avec n_echoes
digFilLen = int(round(dat.getdigfilt()))
TD = int(dat.readacqpar("TD"))
if TD < npoints*2*n_echoes+2*digFilLen:
    n_echoes -= int(2*n_echoes - (TD-2*digFilLen)/npoints) + 1


# reshape FID into 3D array (echo index, echo point index, Re/Im)
if not roundChunk:
    summed = serfile[0:npoints*2*n_echoes].reshape(n_echoes, npoints, 2)
else:
    tmp = serfile.reshape(len(serfile)//2, 2)
    summed = numpy.zeros((n_echoes, npoints, 2))
    for i in range(n_echoes):
        summed[i, :, :] += tmp[int(i*ppc+0.5):int(ppc*i+0.5) + npoints, :]

# create a gaussian apodization function
# time exp(-(at)**2) -> spectral exp(-(w/2a)**2)
#           half width at half maximum GB = a/pi * 2*sqrt(ln(2))
# hence a = GB
# center of gaussian depends on pulse sequence : it can be D6 or D6+D3

#create a gaussian array 
if args.s:
    center = args.s
else:
    center =  (D6+D3)
center_point = center / cycle * npoints
GB = args.gb*math.pi/2.0/math.sqrt(math.log(2.0))
i = numpy.arange(npoints)
apod = numpy.exp(-(1e-6*dw*(i-center_point)*GB)**2)
apod = numpy.resize(apod, (2, npoints))
apod = numpy.swapaxes(apod, 0, 1)

# do the multiplication with gaussian broadening
SUM = summed*apod
SUM = SUM.reshape(n_echoes*npoints, 2)
# separate Re and Im
s1 = SUM[:, 0]
s2 = SUM[:, 1]

# use TDeff parameter to truncate FID
TDeff_par = int(dat.readprocpar("TDeff", status=False))
TDeff =  TDeff_par//2 - digFilLen
if TDeff > 0:
    s1 = s1[0:TDeff]
    s2 = s1[0:TDeff]
else : 
    TDeff = 0

# Apply some zero filling (from SI) and put back digital filter
SI = int(dat.readprocpar("SI", False))
if SI < len(s1)+digFilLen:
    SI =  len(s1)+digFilLen
r1 = numpy.concatenate((numpy.zeros(digFilLen), s1,
            numpy.zeros(SI-len(s1)-digFilLen)))
r2 = numpy.concatenate((numpy.zeros(digFilLen), s2,
            numpy.zeros(SI-len(s2)-digFilLen)))
# ecrit les fichiers 1r 1i
dat.writespect1dri(r1, r2)

# set all optionnal processing parameters to 0
ProcOptions = {"WDW": ["LB", "GB", "SSB", "TM1", "TM2"],
         "PH_mod": ["PHC0", "PHC1"], "BC_mod": ["BCFW", "COROFFS"],
         "ME_mod": ["NCOEF", "LPBIN", "TDoff"], "FT_mod": ["FTSIZE"]}
for par in ProcOptions:
    dat.writeprocpar(par, "0", True, dimension=1)
    for opt in ProcOptions[par]:
        dat.writeprocpar(opt, "0", True, dimension=1)

# write some status processed parameters in procs file so topspin can display
# and process the data properly
dat.writeprocpar("TDeff", str(TDeff_par), True)
dat.writeprocpar("WDW", "1", True)
dat.writeprocpar("LB", str(args.gb), True)

dat.writeprocpar("AXUNIT", "s", True)
dat.writeprocpar("AXRIGHT", str(SI*dw*1e-6), True)

