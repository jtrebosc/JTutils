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
parser  =  argparse.ArgumentParser(description='normalize the noise level to one scan : divide intensity by sqrt(NS)')
parser.add_argument('--ns', type = float, help='Number of scan used for normalization', default=0)
parser.add_argument('infile', help='Full path of the dataset to process')
args  =  parser.parse_args()

#print(args.__dict__)
dat = bruker.dataset(bruker.splitprocpath(args.infile))

if args.ns:
    ns = int(args.ns)
else:
    ns = int(dat.readacqpar("NS",status=True))
# lire la fid et eliminer le filter digital (par defaut)
spect_r, spect_i = dat.readspect1dri()
spect_r /= numpy.sqrt(ns)
spect_i /= numpy.sqrt(ns)
dat.writespect1dri(spect_r, spect_i)

