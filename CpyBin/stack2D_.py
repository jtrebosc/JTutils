#!/usr/bin/python
# -*- coding: utf-8 -*-
# copyright Julien TREBOSC 2012-2013
from __future__ import division

import sys
#import os
#modulePath=os.environ['PYBRUKER']
#sys.path.append(modulePath)
import bruker
import numpy.core as n

def usage():
	print("""transform a 2D processed dataset in a 1D stacked plot""")

# check for unused procno to receive the 1D dataset
# to be done in bruker script
# need two args : 2D source data and 1D dest data

# improvement for bruker library :
# deal with scale and units
# dimensionalite (1D, 2D), 
# axes units (s, Hz, opt)
#AXUNIT
#AXNUC
#AXLEFT
#AXRIGHT
#OFFSET
#SW_p
#FT_mod
#SF
# autres parameters pour interpreter correctement un processed file
#BYTORDP
#NC_proc
#PPARMOD : dimension 0=1D 1=2D 2=3D...

infile = sys.argv[1]
infile1D = sys.argv[2]

# create 1D processed dataset :
# - copy 2D into 1D and adapt proc and procs to 1D
#translate filename into bruker dataset components
data = bruker.splitprocpath(infile)
data1D = bruker.splitprocpath(infile1D)
#initialize dataset
dat = bruker.dataset(data)
dat1D = bruker.dataset(data1D)
#read 2D 2rr data
Fr = "2rr"
Fi = "2ii"
spect = dat.readspect2d(Fr)
specti = dat.readspect2d(Fi)
if specti is None: specti = spect

# convertir F1P,F2P en points:
# divers cas :
# 1) spectres (F1P et F2P en ppm)
# parametres disponibles : OFFSET(valeur gauche) SW_p(largeur spectrale Hz) SF (reference spectrale pour OFFSET) STSI(nbre de points)
# 2) dimension temporelle (F1P, F2P en s)
# parametres disponibles : AXLEFT(valeur gauche) AXRIGHT (valeur droite) STSI(nbre de points)
l1 = float(dat.readprocpar("F1P", False))
l2 = float(dat.readprocpar("F2P", False))

LEFT = float(dat.readprocpar("OFFSET"))
SWH = float(dat.readprocpar("SW_p"))
SF = float(dat.readprocpar("SF"))
AXLEFT = dat.readprocpar("AXLEFT")
AXRIGHT = dat.readprocpar("AXRIGHT")
npoints = float(dat.readprocpar("STSI"))
unit = dat.readprocpar("AXUNIT")
def unit2point(U):
	if unit=="": # unit is ppm
		return int(abs(U-LEFT)/(SWH/SF)*npoints)
	if unit=="s": #unit is second
		return int(abs(U-AXLEFT)/(AXLEFT-AXRIGHT)*npoints)
l2p = unit2point(l2)
l1p = unit2point(l1)

# if indirect dimension is in second then effective max is defined by tdeff
# else if it is Hz or ppm then one must use stsi (already taken when reading spect)

(si1, si) = spect.shape

M = spect.max()

if dat.readprocpar("AXUNIT",True,2) == "s":
#	print(dat.readprocpar("TDeff", True, 2))
	tmp = int(dat.readprocpar("TDeff", True, 2))
	if tmp < si1 : si1 = tmp

#extract sub space
spect1D = spect[0:si1, l1p:l2p].reshape(si1*(l2p-l1p))
spect1Di = specti[0:si1, l1p:l2p].reshape(si1*(l2p-l1p))
dat1D.writespect1dri(spect1D, spect1Di)
dat1D.writeprocpar("AXUNIT", "exp")
dat1D.writeprocpar("AXLEFT", "0.5")
dat1D.writeprocpar("AXRIGHT", str(si1+0.5))

#print(si1,si,l1p,l2p,M)
