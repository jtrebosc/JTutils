#!/usr/bin/python
# -*- coding: utf-8 -*-
# copyright Julien TREBOSC 2012-2013

# calculates (S-S0)/S0 of a 2D dataset
# dataset must be series of 1D spectra alternated S/S0
# if a point of S0 spectrum is below the defined threshold
# then set S0 point to threshold if S0 below threshold
from __future__ import division

import sys
import bruker
import numpy as n

import argparse
parser = argparse.ArgumentParser(description='Calculate (S0-S) spectrum from 2D REDOR or RESPDOR with interleaved acquisition')
parser.add_argument('inputs',help='Full path of the dataset to process')
parser.add_argument('--order','-o',required=False,default='0',help='Order in 2D 0: S0/S or 1: S/S0')
parser.add_argument('--outType','-T',required=False,choices=['S','S0','F'],default='F',help='Output type : [S0|S|F] S0=reference, S=signal,F=(S0-S)')
args=parser.parse_args()
infile=args.inputs
order=args.order
dat=bruker.dataset(bruker.splitprocpath(infile))
spect=dat.readspect2d('2rr')
specti=dat.readspect2d('2ii')
print(spect.shape)
(si1,si2)=spect.shape
print(si2)
spect=spect.reshape(si1/2,2,si2)
specti=specti.reshape(si1/2,2,si2)
if order=='0':
	S0=spect[:,0,:]
	S=spect[:,1,:]
	S0i=specti[:,0,:]
	Si=specti[:,1,:]
elif order=='1':
	S0=spect[:,1,:]
	S=spect[:,0,:]
	S0i=specti[:,1,:]
	Si=specti[:,0,:]
else: raise("order should be 0 (S0-S) or 1 (S-S0)")

out=args.outType
if out=='S':
	Frac=S
	Fraci=Si
elif out=='S0':
	Frac=S0
	Fraci=S0i
elif out=='F':
	Frac=(S0-S)
	Fraci=(S0i-Si)
else : raise('outType should be either S, S0 or F')
dat.writespect2d(Frac,'2rr')
dat.writespect2d(Fraci,'2ii')

