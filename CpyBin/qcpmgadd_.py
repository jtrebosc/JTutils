#!/usr/bin/python
# -*- coding: utf-8 -*-
# copyright Julien TREBOSC 2012-2013
# check that variable PYTHONPATH points to the right folder for bruker.py
#      library

import numpy
import sys
import bruker
import math


# gestion des arguments
import argparse
parser = argparse.ArgumentParser(description='Add echoes in a qcpmg bruker experiment')
parser.add_argument('-l', '--lb', type=float, help='Lorentzian broadening applied to the decaying echo', default=0)
parser.add_argument('-g', '--gb', type=float, help='Gaussian broadening applied to each echo', default=0)
parser.add_argument('-n', type=int, help='Number of echo to sum')
parser.add_argument('-c', type=float, help='qcpmg cycle in us')
parser.add_argument('infile', help='Full path of the dataset to process')
group = parser.add_mutually_exclusive_group()
group.add_argument('-e', action='store_true', help='Sum only even echoes')
group.add_argument('-o', action='store_true', help='Sum only odd echoes')

args = parser.parse_args()
# print bruker.splitprocpath(infile)
dat = bruker.dataset(bruker.splitprocpath(args.infile))

# lire la fid et eliminer le filter digital (par defaut)
serfile = dat.readfid()

# calcule la duree d'un echo en points (a modifier selon le PP utilise)
dw = 1e6/float(dat.readacqpar("SW_h"))
D3 = float(dat.readacqpar("D 3"))*1e6
D6 = float(dat.readacqpar("D 6"))*1e6
P4 = float(dat.readacqpar("P 4"))
P3 = float(dat.readacqpar("P 3"))
L22 = int(dat.readacqpar("L 22"))
if args.n is None or args.n > L22:
    L22 = int(dat.readacqpar("L 22"))+1
else:
    L22 = args.n+1
# calcule le shift du 1er point (delai entre DW_CLK_ON et P4/2 avant RG_ON)
# shift=4.0+P3/2+D6+D3+P4/2.0
shift = 0
# le shift et longueur echo en points
firstP = int(shift/dw*2)
cycle = 2*(D3+D6+2)+P4
cycle = float(args.c)
ppc = cycle/dw
npoints = int(cycle/dw)

if ppc-npoints > 0.001:
    print "Warning echo cycle is not multiple of dwell"
    roundChunk = True
else:
    roundChunk = False

# verifie si TD est coherent avec L22
digFilLen = int(round(dat.getdigfilt()))
TD = int(dat.readacqpar("TD"))
if TD < npoints*2*L22+2*digFilLen:
    L22 -= int(2*L22 - (TD-2*digFilLen)/npoints) + 1

# print digFilLen
# print "dw=%5.3f D3=%5.3f D6=%5.3f P4=%5.3f L22=%d np=%d cy=%5.3f" % (dw, D3,D6,P4,L22,npoints,2*(D3+D6)+P4)

# reshape le ser file en 3D (echo index, echo point index, Re/Im)
if not roundChunk:
    summed = serfile[firstP:firstP+npoints*2*L22].reshape(L22, npoints, 2)
else:
    tmp = serfile.reshape(len(serfile)/2, 2)
    summed = numpy.zeros((L22, npoints, 2))
    for i in range(L22):
        summed[i, :, :] += tmp[firstP+int(i*ppc+0.5):firstP+int(ppc*i+0.5)
                               + npoints, :]

# cree une fonction d'apodisation gaussienne
# temporel exp(-(at)**2) -> spectral exp(-(w/2a)**2)
#           avec largeur mi hauteur GB = a/pi * 2*sqrt(ln(2))
# soit a = GB
apod = numpy.ones((npoints, 2))
GB = args.gb*math.pi/2.0/math.sqrt(math.log(2.0))
for i in range(npoints):
    apod[i][:] = math.exp(-(1e-6*dw*(i-npoints/2.0)*GB)**2)
# do the multiplication with gaussian and lorentzian broadening
LB = args.lb/2
SUME = numpy.zeros((npoints, 2))
SUMA = numpy.zeros((npoints, 2))
for i in range(0, L22):
    if i % 2:
        SUME += summed[i, :, :] * apod*math.exp(-LB*i*npoints*dw*1e-6)
    else:
        SUMA += summed[i, :, :] * apod*math.exp(-LB*i*npoints*dw*1e-6)
if args.e:
    SUM = SUME
elif args.o:
    SUM = SUMA
else:
    SUM = SUMA+SUME

# ecrit le resultat dans les fichiers 1r et 1i:
# separe Re et Im
s1 = SUM[:, 0]
s2 = SUM[:, 1]
# print s1.max(), s2.max()
# print s1.min(), s2.min()

# fait du zero fill pour que topspin puisse processer et
# remet les points correspondant au filtre digital
SI = int(dat.readprocpar("SI", False))
r1 = numpy.concatenate((numpy.zeros(digFilLen), s1,
            numpy.zeros(SI-npoints-digFilLen)))
r2 = numpy.concatenate((numpy.zeros(digFilLen), s2,
            numpy.zeros(SI-npoints-digFilLen)))
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

