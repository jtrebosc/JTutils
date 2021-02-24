#!/usr/bin/python
# -*- coding: utf-8 -*-
# copyright Julien TREBOSC 2012-2013
# check that variable PYTHONPATH points to the right folder for brukerIO.py library

#TODO : check if shift works when STSR/STSI is applied
from __future__ import print_function, division
import numpy
import sys
import brukerIO
import math


# gestion des arguments
import argparse
parser = argparse.ArgumentParser(description='circular shift in F1 by NSP points')
parser.add_argument('-n', type=int, required=True, help='Number of points to shift')
parser.add_argument('infile', help='Full path of the dataset to process')

args = parser.parse_args()
#print(brukerIO.splitprocpath(infile))
dat = brukerIO.dataset(brukerIO.splitprocpath(args.infile))

# 0 undef, 1 QF, 2 QSEQ, 3 TPPI, 4 states, 5 states-tppi, 6 echo=antiecho
mode2D = dat.readacqpar("FnMODE", dimension=2, status=True)

if mode2D == 0:
    mode2D = dat.readprocpar("MC2", dimension=1) + 1
if mode2D == 1:  # QF
    HCsize = 1
elif mode2D in [4, 5, 6]: # States, States-TPPI, Echo/Antiecho
    HCsize = 2
else:
    print("Problem: only QF, States, States-TPPI, Echo-AntiEcho acquisition supported.")
    sys.exit()

if mode2D in [1, ] : # QF only
    files = ['2rr', '2ii']
elif mode2D in [2, 3, 4, 5, 6,]: # states, states-TPPI, Echo-AntiEcho
    files = ['2rr', '2ri', '2ir', '2ii']

# let's shift 2rr but what about the other imaginary ? shift also or HT ?
# lire la fid et eliminer le filter digital (par defaut)
for quadrant in files:
    spect = dat.readspect2d(quadrant)
    spect = numpy.roll(spect, args.n, axis=0)
    dat.writespect2d(spect, quadrant)

# now we need to shift the ppm scale
# get the Hz per point in F1
sw_p = dat.readprocpar("SW_p", dimension=2, status=True)
stsi = dat.readprocpar("STSI", dimension=2, status=True)
hzppt = sw_p/stsi
# get the ppm value of spectrum start (first point high frequency side)
offset = dat.readprocpar("OFFSET", dimension=2, status=True)
# get the SF in F1 to convert Hz to ppm
sf = dat.readprocpar("SF", dimension=2, status=True)
# store the new  ppm value of spectrum start
newoffset = offset+args.n*hzppt/sf
dat.writeprocpar("OFFSET", (newoffset), dimension=2, status=True)

