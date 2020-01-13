#!/usr/bin/python
# -*- coding: utf-8 -*-
# copyright Julien TREBOSC 2012-2013
# check that variable PYTHONPATH points to the right folder for bruker.py
#      library
from __future__ import division

import numpy
import sys
import bruker
import math


# gestion des arguments
import argparse
parser = argparse.ArgumentParser(
  description='Add echoes in a qcpmg bruker experiment')
parser.add_argument('-l', '--lb', type=float, 
          help='Lorentzian broadening applied to the decaying echo', default=0)
parser.add_argument('-g', '--gb', type=float, 
                    help='Gaussian broadening applied to each echo', default=0)
parser.add_argument('-n', type=int, help='Number of echo to sum')
parser.add_argument('-c', type=float, help='qcpmg cycle in us')
parser.add_argument('-s', type=float, 
   help='echo position from start of FID (digital filter excluded) in us')
parser.add_argument('--norm_noise', action='store_true', 
   help='normalise noise level as function of number of echoes', default=False)
parser.add_argument('infile', help='Full path of the dataset to process')
group = parser.add_mutually_exclusive_group()
group.add_argument('-e', action='store_true', help='Sum only even echoes')
group.add_argument('-o', action='store_true', help='Sum only odd echoes')

args = parser.parse_args()
#print(args.__dict__)
dat = bruker.dataset(bruker.splitprocpath(args.infile))

# lire la fid et eliminer le filter digital (par defaut)
serfile = dat.readfid()

# calcule la duree d'un echo en points (a modifier selon le PP utilise)
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

# get the number of echoes: L22+1
n_echoes = int(dat.readacqpar("L 22")) + 1
if args.n and (0 < args.n)  and (args.n <= n_echoes):
    n_echoes = args.n  # in argument is the real number of echoes

# dwell point per cycle : should be integer but may not if improper acquisition parameter used
ppc = cycle/dw
# approximate number of dwell point per cycle
npoints = int(round(cycle/dw))

#print(ppc, npoints, ppc-npoints)
if abs(ppc-npoints) > 0.001:
    print("Warning echo cycle is not multiple of dwell")
    rounding_chunks = True
else:
    rounding_chunks = False

# verifie si TD est coherent avec n_echoes
digFilLen = int(round(dat.getdigfilt()))
TD = int(dat.readacqpar("TD"))
# sometimes TD is too short to contain L22+1 echoes 
# (mostly because of digital filter using some TD points)
if TD < ppc*2*n_echoes+2*digFilLen:
    print("Warning FID cannot hold all echoes : only %d echoes used" % (n_echoes,))
    n_echoes = int((TD-2*digFilLen)/ppc/2)

# reshape FID into 3D array (echo index, echo point index, Re/Im)
if not rounding_chunks:
    summed = serfile[0:npoints*2*n_echoes].reshape(n_echoes, npoints, 2)
else:
    tmp = serfile.reshape(len(serfile)//2, 2)
    summed = numpy.zeros((n_echoes, npoints, 2))
    for i in range(n_echoes):
        summed[i, :, :] += tmp[int(i*ppc+0.5):int(ppc*i+0.5) + npoints, :]

# create a gaussian apodization function
# time exp(-(a(t-center))**2) -> spectral exp(-(w/2a)**2)
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

# do the multiplication with gaussian and lorentzian broadening
LB = args.lb/2
SUME = numpy.zeros((npoints, 2))
SUMA = numpy.zeros((npoints, 2))

L_noise_weight = numpy.zeros(n_echoes)
for i in range(0, n_echoes):
    L_weight = numpy.exp(-LB*i*npoints*dw*1e-6)
    L_noise_weight[i] = L_weight
    if i % 2:
        SUME += summed[i, :, :] * apod * L_weight
    else:
        SUMA += summed[i, :, :] * apod * L_weight
if args.e: # keep only even echoes
    SUM = SUME
elif args.o: # keep only odd echoes
    SUM = SUMA
else:
    SUM = SUMA+SUME

if args.norm_noise:
#    print("normed for noise")
    SUM /= numpy.sqrt(L_noise_weight.sum())
else:
#    print("noise not normed")
    pass

# separate Re and Im
s1 = SUM[:, 0]
s2 = SUM[:, 1]


# Apply some zero filling (from SI) and put back digital filter
SI = int(dat.readprocpar("SI", False))
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
for par in ProcOptions.keys():
    dat.writeprocpar(par, "0", True, dimension=1)
    for opt in ProcOptions[par]:
        dat.writeprocpar(opt, "0", True, dimension=1)

# write some status processed parameters in procs file so topspin can display
# and process the data properly
dat.writeprocpar("WDW", "1", True)
dat.writeprocpar("LB", str(args.gb), True)

dat.writeprocpar("AXUNIT", "s", True)
dat.writeprocpar("AXRIGHT", str(SI*dw*1e-6), True)

