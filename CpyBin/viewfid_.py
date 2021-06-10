#!/usr/bin/python
# -*- coding: utf-8 -*-
# copyright Julien TREBOSC 2012-2021
# check that variable PYTHONPATH points to the right folder for brukerIO.py library

from __future__ import print_function, division

Descript="""
this script reads 2D SER file of NUS acquired dataset. 
Order the row according to nuslist, 
Write to 2rr, 2ir or 2ii files depending on FnMODE
There is a function to plot the result with matplotlib for testing
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
    ax.contour(fid2D, levels=[i*fid2D.max() 
                               for i in numpy.arange(0.03, 1.0, 0.1)])
    p.show()

# manage arguments
import argparse
parser = argparse.ArgumentParser(description='Read Ser file order row according to nuslist. Plot the t1/t2 dataset')
parser.add_argument('-t', '--tdeff', help='Truncate FID according to TDEFF parameter', action='store_true')
parser.add_argument('-s', '--si', help='Truncate or zerofill FID according to SI parameter', action='store_true')
parser.add_argument('-d', '--rmdigfilt', help='Removes the digital filter points', action='store_true')
parser.add_argument('infile', help='Full path of the dataset to process')

args = parser.parse_args()
dat = brukerIO.dataset(brukerIO.splitprocpath(args.infile))

# read ser file 
serfile = dat.readserc(rmGRPDLY=args.rmdigfilt)

td2 = dat.readacqpar("TD", dimension=1, status=True) // 2 # ser is complex number in t2
print(args.tdeff)
if args.tdeff == True: # truncate according to TDeff in direct dim only
    tdeff2 = dat.readprocpar("TDeff", dimension=1, status=False) // 2
    if tdeff2>0 and tdeff2<td2:
        td2 = tdeff2
dat.writeprocpar("TDeff", td2*2, dimension=1, status=True)

if args.rmdigfilt:
    digfilt = dat.getdigfilt()
    td2 -= digfilt

serfile=serfile[:, 0:td2]

# determine the hypercomplex status
FnMode = dat.readacqpar("FnMODE", status=True, dimension=2)
if FnMode == 0:  # if undefined then read MC2 processing parameter 
    # note that MC2 has different meaning : same order as FnMode but with 0 starting for QF
    # hence need to add 1 to MC2 to have same correspondance as for FnMode
    FnMode == dat.readprocpar("MC2", status=False, dimension=2) + 1

td1 = dat.readacqpar("TD", dimension=2, status=True)

if FnMode in [4, 5, 6]:  # State, States-TPPI, Echo-AntiEcho
    HCsize = 2
    td1 = 2*(td1//2)  # one only keeps an even number of rows
    serfile=serfile[0:td1, :]
    names = ['2rr', '2ir']
elif FnMode in [0, 1, 2, 3]:  # undefined, QF, QSEQ, TPPI
    HCsize = 1
    names = ['2rr', '2ii']
    serfile=serfile[0:td1, :]
else:
    raise ValueError("FnMODE is outside acceptable range (0..6)!!! Problem with acqu2s or proc2 file ?")

#check FnTYPE {0: 'traditionnal', 1: 'full(points)', 
#              2:'non_uniform_sampling', 3: 'projection-spectroscopy'} 
FnTYPE = dat.readacqpar("FnTYPE", status=True, dimension=1)
if FnTYPE == 2: # NUS
    sershape = serfile.shape
    serfile = serfile.reshape(sershape[0]//HCsize, HCsize, sershape[-1])
    import os.path
    nuslist = []
    with open(os.path.join(dat.returnacqpath(), 'nuslist')) as f:
        for line in f:
            nuslist.append(int(line.strip()))
    nuslist = nuslist[0:td1//HCsize]
#    print(nuslist)
#    print(sorted(nuslist))
    
# nusTD is original grid max TD/2
#    FullF1TD = dat.readacqpar('NusTD', status=True, dimension=2)
# calculates the max TD grid from max index in recorded nuslist points
    FullF1TD = (max(nuslist)+1)*HCsize
    newser = numpy.zeros((FullF1TD//HCsize, HCsize, sershape[-1]), dtype=serfile.dtype)
#    print(nuslist, serfile.shape)
    newser[nuslist] = serfile
#    for i,j in enumerate(nuslist):
#        newser[j] = serfile[i]
    newser = newser.reshape((FullF1TD, sershape[-1]))
else:
    newser = serfile

# truncate according to TDEFF if required
td1 = newser.shape[0]
# apply the TDeff in F1
if args.tdeff == True:
    tdeff1 = dat.readprocpar("TDeff", dimension=2, status=False)
    if tdeff1 > 0 and tdeff1 < td1:
        td1 = tdeff1
        newser = newser[0:td1, :]
dat.writeprocpar("TDeff", td1, dimension=2, status=True)

if args.si == True:
    SIs = (dat.readprocpar("SI", status=False, dimension=2),
              dat.readprocpar("SI", status=False, dimension=1))
    print("setting SI in F1")
    print("SI1 = ", SIs[0])
    print("td1 = ", td1)
else:
    SIs = newser.shape
shape = brukerIO.SInext(SIs)
newser = brukerIO.zeroFill(newser,shape)
dat.writespectnd(newser.imag, name=names[1])
dat.writespectnd(newser.real, name=names[0])
# set time units
rank = len(newser.shape)
# write some status parameters not already written by writespectnd
for dim in range(1, rank+1):
    dat.writeprocpar("AXUNIT", "s", status=True, dimension=dim)
    dat.writeprocpar("AXLEFT", 0, status=True, dimension=dim)
    swh = dat.readacqpar("SW_h", status=True, dimension=dim)
    si = newser.shape[-dim]
    sfo1 = dat.readacqpar("SFO1", status=True, dimension=dim)
    sf = dat.readprocpar("SF", status=False, dimension=dim)
    dat.writeprocpar("AXRIGHT", (1/swh*(si)/dim), status=True, dimension=dim)
    dat.writeprocpar("OFFSET", ((sfo1+swh/2-sf)/sf), status=True, dimension=dim)
    dat.writeprocpar("SW_p", (swh/sfo1), status=True, dimension=dim)
    dat.writeprocpar("PH_mod", 0, status=True, dimension=dim)
    dat.writeprocpar("BC_mod", 0, status=True, dimension=dim)
    dat.writeprocpar("Mdd_mod", 0, status=True, dimension=dim)

# deal with digital filter for phase correction
dat.writeprocpar("PKNL", args.rmdigfilt, status=True, dimension=1)
# for further processing PKNL should be set to no is digital Filter is removed
dat.writeprocpar("PKNL", not args.rmdigfilt, status=False, dimension=1)

#showser(newser.real)
