#!/usr/bin/python
# -*- coding: utf-8 -*-
# copyright Julien TREBOSC 2012-2013
# check that variable PYTHONPATH points to the right folder for bruker.py library

import numpy
import sys
import bruker
import math


# gestion des arguments
import argparse
parser = argparse.ArgumentParser(description='circular shift in F1 by NSP points')
parser.add_argument('-n',type=int,required=True, help='Number of points to shift')
parser.add_argument('infile',help='Full path of the dataset to process')

args=parser.parse_args()
#print bruker.splitprocpath(infile)
dat=bruker.dataset(bruker.splitprocpath(args.infile))

# let's shift 2rr but what about the other imaginary ? shift also or HT ?
# lire la fid et eliminer le filter digital (par defaut)
spectrr=dat.readspect2d('2rr')
spectri=dat.readspect2d('2ri')
spectir=dat.readspect2d('2ir')
spectii=dat.readspect2d('2ii')

print "shifting axis 0 by n point n=",args.n
spectrr=numpy.roll(spectrr,args.n,axis=0)
spectri=numpy.roll(spectri,args.n,axis=0)
spectir=numpy.roll(spectir,args.n,axis=0)
spectii=numpy.roll(spectii,args.n,axis=0)

dat.writespect2d(spectrr,'2rr')
dat.writespect2d(spectri,'2ri')
dat.writespect2d(spectir,'2ir')
dat.writespect2d(spectii,'2ii')
# not we need to shift the ppm scale
# get the Hz per point in F1
sw_p=float(dat.readprocpar("SW_p",dimension=2,status=True))
stsi=float(dat.readprocpar("STSI",dimension=2,status=True))
hzppt=sw_p/stsi
# get the ppm value of spectrum start (first point high frequency side)
offset=float(dat.readprocpar("OFFSET",dimension=2,status=True))
# get the SF in F1 to convert Hz to ppm
sf=float(dat.readprocpar("SF",dimension=2,status=True))
# store the new  ppm value of spectrum start
newoffset=offset+args.n*hzppt/sf
dat.writeprocpar("OFFSET",str(newoffset),dimension=2,status=True)

