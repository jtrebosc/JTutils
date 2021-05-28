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
parser.add_argument('--MC2', '-m', required=True,
                    default=3, help='MC2 value for storage : 0=QF, 3=States, 4=States-TPPI, 5=echo-antiecho')
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

echo = np.sum((-1)**Q*spect*np.exp(1j*Q*2*np.pi/Phases*
                           np.arange(Phases)[np.newaxis,:,np.newaxis]), axis=1)
antiecho = np.sum((-1)**Q*spect*np.exp(-1j*Q*2*np.pi/Phases*
                           np.arange(Phases)[np.newaxis,:,np.newaxis]), axis=1)

mc2 = int(args.MC2)
SIs = [dat.readprocpar("SI", status=False, dimension=i) for i in (2, 1)]
if mc2 == 0:   # QF
    rows = (echo + antiecho)/2
    #Sx only
    rows = bruker.zeroFill(rows, SIs) #bruker.SInext(Sx.shape))
    dat.writespect2dall([rows.real, rows.imag], MC2=0, dType="tt")
elif mc2 == 3: # States
    rows = np.zeros((si2,2,si3), dtype=complex)
    rows[:,0,:] = (echo + antiecho)/2
    rows[:,1,:] = (echo - antiecho)/(2*1j)
    rows = rows.reshape((si2*2, si3))
    rows = bruker.zeroFill(rows, SIs) #bruker.SInext(Sx.shape))
    dat.writespect2dall([rows.real, rows.imag], MC2=mc2, dType="tt")
elif mc2 == 4: # States-TPPI
    rows = np.zeros((si2,2,si3), dtype=complex)
    rows[:,0,:] = (echo + antiecho)/2
    rows[:,1,:] = (echo - antiecho)/(2*1j)
    rows[1::2,1,:] *= -1   # negates every other Sy row
    rows = rows.reshape((si2*2, si3))
    rows = bruker.zeroFill(rows, SIs) #bruker.SInext(Sx.shape))
    dat.writespect2dall([rows.real, rows.imag], MC2=mc2, dType="tt")
elif mc2 == 5: # echo-antiecho
    rows = np.zeros((si2,2,si3), dtype=complex)
    rows[:,0,:] = echo
    rows[:,1,:] = antiecho
    rows = rows.reshape((si2*2, si3))
    rows = bruker.zeroFill(rows, SIs) #bruker.SInext(Sx.shape))
    dat.writespect2dall([rows.real, rows.imag], MC2=mc2, dType="tt")


