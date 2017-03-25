#!/usr/bin/python
# -*- coding: utf-8 -*-
# copyright Julien TREBOSC 2012-2013

# calculates (S-S0)/S0 of a 2D dataset
# dataset must be series of 1D spectra alternated S/S0
# if a point of S0 spectrum is below the defined threshold
# then set S0 point to threshold if S0 below threshold

import sys
import bruker
import numpy as n

import argparse
parser = argparse.ArgumentParser(description='Calculate (S0-S)/S0 spectrum from 1D REDOR or RESPDOR with interleaved acquisition')
parser.add_argument('inputs',help='Full path of the dataset to process')
parser.add_argument('--threshold','-t',required=True,help='threshold signal below which S0 is not significant')
parser.add_argument('--order','-o',required=False,default='0',help='Order in 2D 0: S0-S / 1: S-S0')
args=parser.parse_args()
infile=args.inputs
threshold=float(args.threshold)
order=args.order
dat=bruker.dataset(bruker.splitprocpath(infile))
spect=dat.readspect1d()
# print("spectrum shape is ",spect.shape)
(si2,)=spect.shape
# print("si2=%d" % (si2,))
spect=spect.reshape(si2/2,2)
if order=='0':
	S0=spect[:,0]
	S=spect[:,1]
elif order=='1':
	S=spect[:,0]
	S0=spect[:,1]
else: raise("order should be 0 (S0-S) or 1 (S-S0)")
	
for i in n.arange(si2/2):
		if S0[i] < threshold : 
		   S0[i]=threshold*10
		   S[i]=threshold*10
		
Frac=(S0-S)/S0
# print "S=",S
# print "S0=",S0
# print "Frac=",Frac
dat.writespect1dri(Frac,Frac)

