#!/usr/bin/python
# -*- coding: utf-8 -*-
# copyright Julien TREBOSC 2012-2013
# check that variable PYTHONPATH points to the right folder for bruker.py library

from __future__ import division

Descript="""
OK so what is this program doing exactly ?
Not much : it reads 2D SER file. Applies apodisation on the t2 time domain.
apodisation is a gaussian whose center follows the slope : t2=+-s*t1.
It writes back into topspin  format for further processing.
"""

import numpy
import sys
import bruker

#def showser(ser):
#    import matplotlib.pyplot as p
#    p.imshow(ser)
#    p.show()

# manage arguments
import argparse
parser = argparse.ArgumentParser(description='Read Ser file and apply 2D apodisation (LB along t1 and GB along F2. GB is centered at t2=s*t1+c')
#parser.add_argument('-l', '--lb', type=float,  help='Lorentzian broadening (Hz FWHM) applied along F1', default=0)
parser.add_argument('-g', '--gb', type=float,  help='Gaussian broadening (Hz FWHM) applied along t2 centered at t2=s*t1+c', default=0)
parser.add_argument('-s', type=float,  help='s=t2/t1 slope to follow for GB center', default=0)
parser.add_argument('-c', type=float,  help='initial center position (at row 0) in us excluding digital filter delay', default=0)
parser.add_argument('-e', '--echoOnly', action='store_true', help='Apodize only along the echo signal (positive slope)')
parser.add_argument('infile', help='Full path of the dataset to process')

args = parser.parse_args()
#print(bruker.splitprocpath(infile))
dat = bruker.dataset(bruker.splitprocpath(args.infile))

# read ser file 
serfile = dat.readserc(rmGRPDLY=False)

# calculates useful boudaries from TDeff and SI
(td1, td2c) = serfile.shape
print("td1=%d, td2c=%d" % (td1, td2c))
tdeff2 = dat.readprocpar("TDeff", status=False, dimension=1)
tdeff1 = dat.readprocpar("TDeff", status=False, dimension=2)
SI2 = dat.readprocpar("SI", False, 1)
SI1 = dat.readprocpar("SI", False, 2)
if 0 < tdeff1 and tdeff1 < td1:
    td1 = tdeff1
if SI1 < td1//2:
    td1 = 2*SI1
if 0 < tdeff2 and tdeff2 < 2*td2c:
    td2c = tdeff2//2
if SI2 < td2c:
    td2c=SI2

print("td1=%d, tdeff1=%d, si1=%d" % (td1, tdeff1, SI1))
print("td2=%d, tdeff2=%d, si2=%d" % (td2c, tdeff2, SI2))
serfile = serfile[0:td1, 0:td2c]

mode2D = {'1': 'QF' , '2': 'QSEQ', '3': 'TPPI', 
          '4': 'States', '5': 'States-TPPI', '6': 'Echo-AntiEcho' }

# reshape data according to FnMODE
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
    print("FnMODE is outside acceptable range (0..6)!!! Problem with acqu2s or proc2 file")

serfile = serfile.reshape((td1//HCsize, HCsize, td2c))
serfile = numpy.swapaxes(serfile, 0, 1)  # serfile shape is HCsize, td1//2, td2c)

sw2 = dat.readacqpar("SW_h", status=True, dimension=1)
sw1 = dat.readacqpar("SW_h", status=True, dimension=2)
dw2 = 1.0/sw2
dw1 = 1.0/sw1
# special case of TPPI on dwell with respect to SW
if FnMode == 3:
    dw1 /= 2  # if TPPI dw = 0.5 / swh

# create a gaussian apodization function in time domain
# time : exp(-(at)**2) --FT-->  frequency : exp(-(f/2a)**2) with width at half maximum GB = a/pi * 2*sqrt(ln(2))
# hence a = GB*pi/2/sqrt(ln(2))

def gauss(gb, t, t0):
	g = gb*numpy.pi/2.0/numpy.sqrt(numpy.log(2.0))
	return numpy.exp(-(g*(t-t0))**2)

# also define a lorentzian function
def lorentz(lb, t, t0):
	return numpy.exp(-numpy.pi*lb*abs(t-t0))

# calculate center point
digfilt=dat.getdigfilt()
centerpoint = args.c/dw2/1e6 + digfilt

# create a mesh index matrix
OI = numpy.ones(td2c).reshape((1, td2c))
I = numpy.arange(td2c).reshape((1, td2c)) - centerpoint
OJ = numpy.ones(td1//HCsize).reshape((td1//HCsize, 1))
J = numpy.arange(td1//HCsize).reshape((td1//HCsize, 1))
#2D array (td1//HCsize, td2c) representing the time t for gaussian apodization
Tg = numpy.dot(OJ, I*dw2)
#2D array (td1//HCsize, td2c) representing the time t0 for gaussian apodization along +s (T0gp) and -s (T0gm)
T0gp = numpy.dot( J*dw1*args.s, OI)
T0gm = numpy.dot(-J*dw1*args.s, OI)
#2D array (td1//HCsize, td2c) representing the time t for lorentzian apodization in F1
#Tl = numpy.dot(dw1*J, OI)
#2D array (td1//HCsize, td2c) representing the time t0 for lorentzian apodization
#T0l = numpy.zeros((td1//HCsize, td2c))-centerpoint*dw2
# generates the Gaussian function array
if args.echoOnly:
    G = gauss(args.gb, Tg, T0gp)
else:
    G = numpy.maximum(gauss(args.gb, Tg, T0gp), gauss(args.gb, Tg, T0gm))
# Apodization array
ApodArray = G # *lorentz(args.lb, Tl, T0l)

#apply apodization (use auto expansion of ApodArray for summed(:, ...) first dimension)
SUM = serfile*ApodArray  # multiply with broadcasting on HCsize dimension

SUM = numpy.swapaxes(SUM, 0, 1).reshape((td1, td2c))

# Apply zero filling according to final size SI1, SI2 from topspin processing parameters
rr = bruker.pad(SUM, ((0, SI1-td1), (0, SI2-td2c)), 'constant')
print("rr shape is ", rr.shape)

# set all optionnal processing parameters to 0
ProcOptions = {"WDW": [["LB", 0], ["GB", 0], ["SSB", 0], ["TM1", 0], ["TM2", 0]],
               "PH_mod": [["PHC0", 0], ["PHC1", 0]], "BC_mod": [["BCFW", 0], ["COROFFS", 0]],
               "ME_mod": [["NCOEF", 0], ["LPBIN", 0], ["TDoff", 0]], "FT_mod": [["FTSIZE", 0], ["FCOR", 0],
               ["STSR", 0], ["STSI", 0], ["REVERSE", False]],
              }
for dim in [1, 2]:
    for par in ProcOptions:
        dat.writeprocpar(par, 0, status=True, dimension=dim)
        for opt in ProcOptions[par]:
            dat.writeprocpar(opt[0], opt[1], status=True, dimension=dim)

# write 2rr and 2ir files in time/time mode : SI, STSI and some other parameters are set automatically

if FnMode in [1]:  # QF
    imag_file = '2ii'
elif FnMode in [2, 3, 4, 5, 6]:  # QSEQ, TPPI, State, States-TPPI, Echo-AntiEcho
    imag_file = '2ir'

dat.writespect2d(rr.real, "2rr", "tt")
dat.writespect2d(rr.imag, imag_file, "tt")


# digital filter is not removed: PKNL must be set to False
dat.writeprocpar("PKNL", "no", status=True)
dat.writeprocpar("WDW", 2, status=True)
dat.writeprocpar("LB", (-args.gb), status=True)
dat.writeprocpar("GB", 0, status=True)
# unselect apodization for further processing
dat.writeprocpar("WDW", 0, status=False)

