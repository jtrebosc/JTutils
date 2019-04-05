#!/usr/bin/python
# -*- coding: utf-8 -*-
# copyright Julien TREBOSC 2012-2013
# check that variable PYTHONPATH points to the right folder for
# bruker.py library

from __future__ import division
import numpy
import sys
import bruker
import math


# gestion des arguments
import argparse
parser = argparse.ArgumentParser(description='Add echoes in a (Hypercomplex) 2D qcpmg bruker experiment')
parser.add_argument('-l', '--lb', type=float,
          help='Lorentzian broadening applied to the decaying echo', default=0)
parser.add_argument('-g', '--gb', type=float,
          help='Gaussian broadening applied to each echo', default=0)
parser.add_argument('-n', type=int, help='Number of echo to sum')
parser.add_argument('-s', '--slope', type=float,
          help='t2/t1 slope along which the echoes are shifting', default=0)
parser.add_argument('-c', type=float,
          help='qcpmg cycle in us')
group = parser.add_mutually_exclusive_group()
group.add_argument('-e', action='store_true', help='Sum only even echoes')
group.add_argument('-o', action='store_true', help='Sum only odd echoes')

parser.add_argument('infile', help='Full path of the dataset to process')

args = parser.parse_args()
# print(bruker.splitprocpath(infile))
dat = bruker.dataset(bruker.splitprocpath(args.infile))

"""
A faire :
    ser file reshape en 4 dim (F1, HCF1(re/im), F2, HCF2(re/im))
    note : en QF HCF1 a une dimension de 1
    Le splitting en echoes sur F2 peut se faire sous la forme
    F1, HCF1(re/im), NEchoes, F2, HCF2(re/im)
"""
# check dataset is 2D:
if int(dat.readacqpar("PARMODE")) != 1:
    print("dataset is not 2D : exiting...")
    sys.exit()

# 0 undef, 1 QF, 2 QSEQ, 3 TPPI, 4 states, 5 states-tppi, 6 echo=antiecho
mode2D = int(dat.readacqpar("FnMODE", dimension=2, status=True))

if mode2D == 0:
    mode2D = int(dat.readprocpar("MC2"))+1
if mode2D == 1:
    HCsize = 1
elif mode2D in [2, 3, 4, 5, 6]:
    HCsize = 2
else:
    print("""Whoaoo, problem. Cannot determine wether F1 is 
          hypercomplex or not. Please fix FnMODE or MC2""")
    sys.exit()


# lire la fid et eliminer le filter digital (par defaut)
serfile = dat.readser()
# fcor = float(dat.readprocpar("FCOR"))
# fcor1 = float(dat.readprocpar("FCOR", dimension=2))
# serfile[0, :] *= fcor1
# serfile[1, :] *= fcor1
# serfile[:, 0] *= fcor1
# serfile[:, 1] *= fcor1

# calcule la duree d'un echo en points (a modifier selon le PP utilise)
dw = 1e6/float(dat.readacqpar("SW_h"))
dw1 = 1e6/float(dat.readacqpar("SW_h", dimension=2))

# nombre de points par cycle
cycle = args.c
if not cycle:
    cycle = float(dat.readacqpar("P 60"))  # for pp where cycle is stored in P_60
    if cycle < 0.1:  # for old
        D3 = float(dat.readacqpar("D 3"))*1e6
        D6 = float(dat.readacqpar("D 6"))*1e6
        P180 = float(dat.readacqpar("P 2"))
        cycle = 2*(D3+D6)+P180

# how many echoes to add ?
nEchoes = int(dat.readacqpar("L 22"))+1
if args.n is None or args.n > nEchoes:
    "pass"
else:
    nEchoes = args.n

shift = 0
# le shift et longueur echo en points
firstP = int(shift/dw*2)

ppc = (cycle)/dw
# oneEchoSize=int(round((2*(D3+D6)+P2)/dw))
oneEchoSize = int(round(cycle/dw))
if abs(ppc-oneEchoSize) > 0.001:
    print("Warning echo cycle is not multiple of dwell")
    chunkNotRound = True
else:
    chunkNotRound = False

# Check that TD can accomodate L22+1 echoes
digFilLen = int(round(dat.getdigfilt()))
TD = int(dat.readacqpar("TD"))
if TD < 2*oneEchoSize*nEchoes+2*digFilLen:
    nEchoes = (TD//2-digFilLen)//oneEchoSize
    print("""WARNING : FID is not long enough for L22 echo + 1. 
           Actually using  %s echoes""" % (nEchoes,))

# size of 2D array in t1
TD1 = int(dat.readacqpar("TD", status=True, dimension=2))
# TD1 is rounded to multiple of HCsize
TD1 = TD1//HCsize*HCsize
serfile = serfile[0:TD1]
#print("HCsize=", HCsize)
#print("TD1=", TD1)

#print(digFilLen)
# print("dw=%5.3f D3=%5.3f D6=%5.3f P2=%5.3f L22=%d np=%d cy=%5.3f" %
# (dw,D3,D6,P2,nEchoes,oneEchoSize,2*(D3+D6)+P2))

# reshape le ser file en 5D (TD1//HCsize, HCsize(F1) , echo index,
# echo point index, Re/Im)
if not chunkNotRound:
#    print(serfile[:, firstP:firstP+oneEchoSize*2*nEchoes].shape, TD1//HCsize*HCsize, nEchoes*oneEchoSize*2)
#    print(serfile.shape, firstP, firstP+oneEchoSize, nEchoes, (TD1//HCsize, HCsize, nEchoes, oneEchoSize, 2))
    summed = serfile[:, firstP:firstP+oneEchoSize*2*nEchoes].reshape(TD1//HCsize, HCsize, nEchoes, oneEchoSize, 2)
else:
    (si1, si) = serfile.shape
#    print((si1, si), (TD1//HCsize, HCsize, si//2, 2),
#          len(serfile), len(serfile//TD1//2))
    tmp = serfile.reshape(TD1//HCsize, HCsize, si//2, 2)
    summed = numpy.zeros((TD1//HCsize, HCsize, nEchoes, oneEchoSize, 2))
    for i in range(nEchoes):
        summed[:, :, i, :, :] += tmp[:, :,
                                     firstP+int(i*ppc+0.5):
                                     firstP+int(ppc*i+0.5)+oneEchoSize, :]
# trunc SER file according to TDeff :
TDeff1 = (int(dat.readprocpar("TDeff", status=False, dimension=2)
              )//HCsize)*HCsize
if TDeff1 > 0 and TDeff1 < TD1:
    TD1 = TDeff1
    summed = summed[:TD1//HCsize]
#print(summed.shape)

# cree une fonction d'apodisation gaussienne
# temporel exp(-(at)**2) -> spectral exp(-(w/2a)**2) avec largeur mi hauteur
# GB = a/pi * 2*sqrt(ln(2))
# soit a=GB

# il faut prévoir une double apodization avec une pente +-p réglable.
# la 2D suppose States

# calcule la matrice d'apodization composée de deux gaussiennes dont les centres
# se décalent avec t1 dans un rapport +-1 (1Q) ou +-2 (DQ)
# NE PAS utiliser fromfunction (pas performant)
# generer deux tables (A et B) avec les deux gaussiennes qui shiftent,
# prendre le max elt par elt de A et B

# GB : from gb (fwhh of gaussian in frequency domain) for use in time
# domain multiplication by exp(-(x*GB)^2)
GB = args.gb*math.pi/2.0/math.sqrt(math.log(2.0))
# the slope (t2/t1) along which the E/AE shifts with t1
expRatio = args.slope

# create array with x
t2_ind = numpy.arange(-oneEchoSize/2, oneEchoSize/2)*(1e-6*dw*GB)
t2_ind2d = numpy.resize(t2_ind, (TD1//HCsize, oneEchoSize))
# create array with |x0| shift
t1_ind = numpy.arange(TD1/HCsize)*(1e-6*dw1*expRatio*GB)
t1_ind2d = numpy.resize(t1_ind, (oneEchoSize, TD1//HCsize))
t1_ind2d = t1_ind2d.T

# gaussian with positive t1 shift
G_p = numpy.exp(-(t2_ind2d-t1_ind2d)**2)
# gaussian with positive t1 shift
G_m = numpy.exp(-(t2_ind2d+t1_ind2d)**2)
# Gaussian function max of G_p or G_m
G = numpy.maximum(G_p, G_m)

# extend apodization matrix with n echoes with LB
LG = numpy.resize(G, (nEchoes, TD1//HCsize, oneEchoSize)).swapaxes(0, 1)
# LG is now (TD1/2, necho, oneEchoSize) shape
LB = 0.1
L = numpy.exp(numpy.arange(nEchoes)*(-LB*1e-6*dw*oneEchoSize))
LG *= L[numpy.newaxis, :, numpy.newaxis]


# apply apodization for each hypercomplex component
for f1HC in range(HCsize):
    for f2HC in range(2):
        summed[:, f1HC, :, :, f2HC] *= LG
        # print(LG.shape, summed[:, i, :, :, j].shape)
# sum echoes odd, even or all
if args.o:  # add only odd echoes (start 1) :
    a = 0
    c = 2
elif args.e:  # add only even echoes (start 1) :
    a = 1
    c = 2
else:  # add all echoes
    a = 0
    c = 1

SUM = summed[:, :, a::c, :, :].sum(axis=2).reshape(TD1, oneEchoSize, 2)

# ecrit le resultat dans les fichiers 2rr et 2ri :
# separe Re et Im et remet
s1 = SUM[..., 0]
s2 = SUM[..., 1]
# print(s1.max(), s2.max())
# print(s1.min(), s2.min())


# fait du zero fill pour que topspin puisse processer et
# remet les points correspondant au filtre digital
SI = int(dat.readprocpar("SI", False))
SI1 = int(dat.readprocpar("SI", status=False, dimension=2))
# RAJOUTER ZEROFILL t1
# digFilLen=0
#print(digFilLen)
r1 = numpy.hstack((numpy.zeros((TD1, digFilLen)), s1,
                   numpy.zeros((TD1, SI-oneEchoSize-digFilLen))))
r2 = numpy.hstack((numpy.zeros((TD1, digFilLen)), s2,
                   numpy.zeros((TD1, SI-oneEchoSize-digFilLen))))
r1 = numpy.vstack((r1, numpy.zeros((SI1-TD1, SI))))
r2 = numpy.vstack((r2, numpy.zeros((SI1-TD1, SI))))
#print(r1.shape, r2.shape)

fnmode = dat.readacqpar("FnMODE", status=True, dimension=1)

if fnmode in "0 1 2 3" : # QF
    imag_file = '2ii'
elif fnmode in "4 5 6":
    imag_file = '2ir'
# ecrit les fichiers 1r 1i
dat.writespect2d(r1, name="2rr", dType="tt")
dat.writespect2d(r2, name=imag_file, dType="tt")
# write some status processed parameters in procs file so topspin can display
# and process the data properly

dat.writeprocpar("PKNL", "no", status = True)
# dat.writeprocpar("PKNL", "no", status = False)

# set all optionnal processing parameters to 0
ProcOptions = {"WDW": ["LB", "GB", "SSB", "TM1", "TM2"],
               "PH_mod": ["PHC0", "PHC1"], "BC_mod": ["BCFW", "COROFFS"],
               "ME_mod": ["NCOEF", "LPBIN", "TDoff"], "FT_mod": ["FTSIZE", "FCOR"]}
for dim in [1, 2]:
    for par in ProcOptions.keys():
        dat.writeprocpar(par, "0", True, dimension=dim)
        for opt in ProcOptions[par]:
            dat.writeprocpar(opt, "0", True, dimension=dim)
# need to deal with TDoff. Although not used in time domain  for indirect dimension it must be copied for further processing
TDoff = dat.readprocpar("TDoff", status=False, dimension=2)
dat.writeprocpar("TDoff", TDoff, status=True, dimension=2)

# even though we are in time domain we need to set a SW_p in ppm
# with respect to irradiation frequency SFO1
# otherwise the OFFSET is not properly calculated in further 
# topspin calculations especially in indirect dimension...
sw1 = float(dat.readacqpar("SW_h", status=True, dimension=2))
sfo1 = float(dat.readacqpar("SFO1", status=True, dimension=2))
sw2 = float(dat.readacqpar("SW_h", status=True, dimension=1))
sfo2 = float(dat.readacqpar("SFO1", status=True, dimension=1))
dat.writeprocpar("SW_p", str(sw2/sfo2), status=True,dimension=1)
dat.writeprocpar("SW_p", str(sw1/sfo1), status=True,dimension=2)

# adjust the WDW in F2 since we applied some GB/LB
dat.writeprocpar("WDW", "1", True, 1)
dat.writeprocpar("LB", str(args.gb), True, 1)

dat.writeprocpar("AXUNIT", "s", True)
dat.writeprocpar("AXUNIT", "s", True, dimension=1)
dat.writeprocpar("AXRIGHT", str(SI*dw*1e-6), True)
dat.writeprocpar("AXRIGHT", str(SI1/2*dw1*1e-6), True, dimension=2)
