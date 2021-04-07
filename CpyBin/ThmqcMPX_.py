#!/usr/bin/python
# -*- coding: utf-8 -*-
# copyright Julien TREBOSC 2021

# calculates phase cycling from multiplex experiment
# calculate echoe and anti echoe then store back in E/AE 
# fashion in topspin

from __future__ import division, print_function

import sys
import brukerIO as bruker
import numpy as np

import argparse
parser = argparse.ArgumentParser(description='Calculate phase cycled signal from multiplexed 2D')
parser.add_argument('input', help='Full path of the dataset to process')
parser.add_argument('--Qlevel', '-Q', required=True,
                    default=1, help='Quantum level to be cycled')
#parser.add_argument('--Phases', '-P', required=False, default=8,
#                    help='Number of multiplexed phases')
args = parser.parse_args()
infile = args.input
Q = float(args.Qlevel)

dat = bruker.dataset(bruker.splitprocpath(infile))

# assume that XF2 is performed with E/AE processing hence producing 2rr and 2ir files
spect = dat.readserc(rmGRPDLY=False)

(si2, Phases, si3) = spect.shape
#tdeff = int(dat.readprocpar("TDeff", True, dimension=2))

echo = np.sum((-1)**Q*spect*
              np.exp(-1j*2.0*np.pi*np.arange(Phases)[np.newaxis,:,np.newaxis]*
              Q/Phases), axis=1)
antiecho = np.sum((-1)**Q*spect*
          np.exp(1j*2.0*np.pi*np.arange(Phases)[np.newaxis,:,np.newaxis]*
          Q/Phases), axis=1)

Sx = (echo + antiecho)/2
SIs = [dat.readprocpar("SI", status=False, dimension=i) for i in (2, 1)]
Sx = bruker.zeroFill(Sx, SIs) #bruker.SInext(Sx.shape))
dat.writespect2dall([Sx.real, Sx.imag], MC2=0, dType="tt")
#dat.writespect2d(out.real, '2rr')
#dat.writespect2d(out.imag, '2ir')
#dat.writeprocpar("TDeff", str(rows), True, dimension=2)

