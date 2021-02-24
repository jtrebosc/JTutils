#!/usr/bin/python
# -*- coding: utf-8 -*-
# copyright Julien TREBOSC 2012-2021
# check that variable PYTHONPATH points to the right folder for brukerIO.py library

from __future__ import print_function, division

Descript="""
OK so what is this program doing exactly ?
Not much : it reads 2D SER file of NUS acquired dataset. 
Order the row according to nuslist
plot the result 
"""

import numpy
import sys
import brukerIO

def showser(fid2D):
    import matplotlib.pyplot as p
    fig, ax = p.subplots()
    ax.set_xlabel("F2/points")
    ax.set_ylabel("F1/points")
    ax.set_xlim(0,fid2D.shape[-1])
    ax.set_ylim(0,fid2D.shape[0])
    ax.contour(fid2D, levels=[i*fid2D.max() for i in numpy.arange(0.03, 1.0, 0.1)])

    p.show()

# manage arguments
import argparse
parser = argparse.ArgumentParser(description='Read Ser file order row according to nuslist. Plot the t1/t2 dataset')
parser.add_argument('infile', help='Full path of the dataset to process')

args = parser.parse_args()
dat = brukerIO.dataset(brukerIO.splitprocpath(args.infile))

# read ser file 
serfile = dat.readserc(rmGRPDLY=False)
# determine the hypercomplex status
FnMode = dat.readacqpar("FnMODE", status=True, dimension=2)
if FnMode == 0:  # if undefined then read MC2 processing parameter 
    # note that MC2 has different meaning : same order as FnMode but with 0 starting for QF
    # hence need to add 1 to MC2 to have same correspondance as for FnMode
    FnMode == dat.readprocpar("MC2", status=False, dimension=2) + 1

if FnMode in [4, 5, 6]:  # State, States-TPPI, Echo-AntiEcho
    HCsize = 2
    td1 = 2*(td1//2)  # one only keeps an even number of rows
    serfile=serfile[0:td1, :]
elif FnMode in [0, 1, 2, 3]:  # undefined, QF, QSEQ, TPPI
    HCsize = 1
else:
    raise ValueError("FnMODE is outside acceptable range (0..6)!!! Problem with acqu2s or proc2 file ?")


#check FnTYPE {0: 'traditionnal', 1: 'full(points)', 
#              2:'non_uniform_sampling', 3: 'projection-spectroscopy'} 
FnTYPE = dat.readacqpar("FnTYPE", status=True, dimension=1)
if FnTYPE == 2: # NUS
    sershape = serfile.shape
    FullF1TD = dat.readacqpar('NusTD', status=True, dimension=2)
    serfile = serfile.reshape(sershape[0]//HCsize, HCsize, sershape[-1])
    import os.path
    nuslist = []
    with open(os.path.join(dat.returnacqpath(), 'nuslist')) as f:
        for line in f:
            nuslist.append(int(line.strip()))
    print(nuslist)
    print(sorted(nuslist))
    newser = numpy.zeros((FullF1TD//HCsize, HCsize, sershape[-1]), dtype=serfile.dtype)
    newser[nuslist] = serfile
#    for i,j in enumerate(nuslist):
#        newser[j] = serfile[i]
    newser = newser.reshape((FullF1TD, sershape[-1]))
else:
    newser = serfile

shape = brukerIO.SInext(newser.shape)
newser = brukerIO.zeroFill(newser,shape)
dat.writespectnd(newser.imag, name='2ir')
dat.writespectnd(newser.real)
# set time units
rank = len(shape)
for dim in range(1, rank+1):
    dat.writeprocpar("AXUNIT", "s", status=True, dimension=dim)
    dat.writeprocpar("AXLEFT", 0, status=True, dimension=dim)
    swh = dat.readacqpar("SW_h", status=True, dimension=dim)
    si = shape[-dim]
    sfo1 = dat.readacqpar("SFO1", status=True, dimension=dim)
    sf = dat.readprocpar("SF", status=False, dimension=dim)
    dat.writeprocpar("AXRIGHT", (1/swh*(si)/dim), status=True, dimension=dim)
    dat.writeprocpar("OFFSET", ((sfo1+swh/2-sf)/sf), status=True, dimension=dim)
    dat.writeprocpar("SW_p", (swh/sfo1), status=True, dimension=dim)
    dat.writeprocpar("PKNL", "no", status=True, dimension=dim)
    dat.writeprocpar("Mdd_mod", 0, status=True, dimension=dim)

#showser(newser.real)
