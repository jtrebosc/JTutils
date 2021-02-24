#!/usr/bin/python
# -*- coding: utf-8 -*-
# copyright Julien TREBOSC 2012-2013
# check that variable PYTHONPATH points to the right folder for brukerIO.py
#      library
from __future__ import division, print_function

import numpy
import sys
import brukerIO
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
parser.add_argument('-t', type=int, 
   help='number of point to discard at start of echo to remove dead time.')
parser.add_argument('infile', help='Full path of the dataset to process')

args = parser.parse_args()
dat = brukerIO.dataset(brukerIO.splitprocpath(args.infile))

# read FID file (digital filter is removed by default)
serfile = dat.readfid()

# calculate duration of an echo in point unit
dw = 1e6/dat.readacqpar("SW_h")
P60 = dat.readacqpar("P 60") # should store the cycle time
# in case cycle time is not stored in P60, this program uses a default
# calculation based on D3, D6, P4, P3
D3 = dat.readacqpar("D 3")*1e6
D6 = dat.readacqpar("D 6")*1e6
P4 = dat.readacqpar("P 4")
P3 = dat.readacqpar("P 3")
# cycle is set to a
if args.c : # one can provide the cycle in argument
    cycle = float(args.c)
elif P60 > 0: # pulse program should store status cycle in P60
    cycle = P60
else : # default behavior may depend on pulse program implementation
    cycle = 2*(D3+D6+2)+P4

if args.t:
    dead_pts = args.t
else: 
    dead_pts = int(dat.readprocpar("TDoff", status=False))

# get the number of echoes
n_echoes = dat.readacqpar("L 22") + 1

ppc = cycle/dw
npoints = int(round(cycle/dw))

if ppc-npoints > 0.001:
    print("Warning echo cycle is not multiple of dwell")
    roundChunk = True
else:
    roundChunk = False

# Check if TD is consistent with n_echoes
digFilLen = int(round(dat.getdigfilt()))
TD = dat.readacqpar("TD")
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

#print("zeroes the initial %d dead_pts" % (dead_pts,))
if dead_pts != 0:
    SUM[:,0:dead_pts,:] = 0.0
    SUM[:,-dead_pts:,:] = 0.0

SUM = SUM.reshape(n_echoes*npoints, 2)
# separate Re and Im
s1 = SUM[:, 0]
s2 = SUM[:, 1]

# use TDeff parameter to truncate FID
TDeff_par = dat.readprocpar("TDeff", status=False)
TDeff =  TDeff_par//2 - digFilLen
if TDeff > 0:
    s1 = s1[0:TDeff]
    s2 = s1[0:TDeff]
else : 
    TDeff = 0

# Apply some zero filling (from SI) and put back digital filter
SI = dat.readprocpar("SI", False)
if SI < len(s1)+digFilLen:
    SI =  brukerIO.SInext(len(s1)+digFilLen)
r1 = numpy.zeros(SI)
r1[digFilLen:digFilLen+s1.size] = s1
r2 = numpy.zeros(SI)
r2[digFilLen:digFilLen+s2.size] = s2
# write spectrum in dataset (files 1r and 1i)
dat.writespect1dri(r1, r2)

# set all optionnal processing parameters to 0
ProcOptions = {"WDW"   : [["LB", 0], ["GB", 0], ["SSB", 0], ["TM1", 0], ["TM2", 0]],
               "PH_mod": [["PHC0", 0], ["PHC1", 0]], "BC_mod": [["BCFW", 0], ["COROFFS", 0]],
               "ME_mod": [["NCOEF", 0], ["LPBIN", 0], ["TDoff", 0]], 
               "FT_mod": [["FTSIZE", 0], ["FCOR", 0], ["STSR", 0], ["STSI", 0], ["REVERSE", False]],
              }

for par in ProcOptions:
    dat.writeprocpar(par, 0, True, dimension=1)
    for opt in ProcOptions[par]:
        dat.writeprocpar(opt[0], opt[1], True, dimension=1)

# write some status processed parameters in procs file so topspin can display
# and process the data properly
dat.writeprocpar("TDeff", (TDeff_par), True)
dat.writeprocpar("WDW", 1, True)
dat.writeprocpar("LB", (args.gb), True)

dat.writeprocpar("AXUNIT", "s", True)
dat.writeprocpar("AXRIGHT", (SI*dw*1e-6), True)

