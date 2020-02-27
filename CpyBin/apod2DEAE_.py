#!/usr/bin/python
# -*- coding: utf-8 -*-
# copyright Julien TREBOSC 2012-2013
# check that variable PYTHONPATH points to the right folder for bruker.py library

from __future__ import division

Descript="""
OK so what is this program doing exactly ?
Not much : it reads 2D SER file. Turn it into Hypercomplex data and applies apodisation on the t2 time domain.
apodisation is a gaussian whose center follows the slope : t2=+-s*t1.
It writes back into topspin  format for further processing.
One question is how topsin determine the data format storage:
once processed data are at least stored in 2 files with reals and imaginaries.
son one always find 2rr and 2ii or 2ir at least
"""

import numpy
import sys
import bruker
import math

def showser(ser):
    import matplotlib.pyplot as p
    p.imshow(ser)
    p.show()

# manage arguments
import argparse
parser = argparse.ArgumentParser(description='Read Ser file and apply 2D apodisation (LB along t1 and GB along F2. GB is centered at t2=s*t1')
parser.add_argument('-l', '--lb', type=float, help='Lorentzian broadening (Hz) applied along F1', default=0)
parser.add_argument('-g', '--gb', type=float, help='Gaussian broadening (Hz) applied along t2 centered at t2=s*t1', default=0)
parser.add_argument('-s', type=float, help='s=t2/t1 slope to follow for GB center')
parser.add_argument('-c', type=float,  help='initial center position (at row 0) in us excluding digital filter delay', default=0)
parser.add_argument('infile', help='Full path of the dataset to process')

args = parser.parse_args()
#print(bruker.splitprocpath(infile))
dat = bruker.dataset(bruker.splitprocpath(args.infile))

# read ser file and correct automatically for digital filter
serfile = dat.readserc(rmGRPDLY=False)

# calculates useful boudaries from TDeff and SI
(td1, td2c) = serfile.shape

mode2D = {'1': 'QF' , '2': 'QSEQ', '3': 'TPPI', 
          '4': 'States', '5': 'States-TPPI', '6': 'Echo-AntiEcho' }

# reshape data according to FnMODE
FnMode = dat.readacqpar("FnMODE", status=True, dimension=2)
if FnMode in "0 1 2 3":
    print("data cannot be made in Echo/AntiEcho format: TPPI not handled")
    sys.exit()
if FnMode == "0":  # if undefined then read MC2 processing parameter 
    # note that MC2 has different meaning : same order as FnMode but with 0 starting for QF
    # hence need to add 1 to MC2 to have same correspondance as for FnMode
    FnMode == str(int(dat.readprocpar("MC2", status=False, dimension=2)) + 1) 

if FnMode in "4 5 6":  # State, States-TPPI, Echo-AntiEcho
    HCsize = 2
    td1 = 2*(td1//2)  # one only keeps an even number of rows
    serfile = serfile[0:td1, :]
elif FnMode in "0 1 2 3":  # undefined, QF, QSEQ, TPPI
    HCsize = 1
else:
    print("FnMODE is outside acceptable range (0..6)!!! Problem with acqu2s or proc2 file")

# trunc to TDeff
tdeff2 = int(dat.readprocpar("TDeff", status=False, dimension=1))
tdeff1 = int(dat.readprocpar("TDeff", status=False, dimension=2))
SI2 = int(dat.readprocpar("SI", False, 1))
SI1 = int(dat.readprocpar("SI", False, 2))
if 0 < tdeff1 and tdeff1 < td1:
    td1 = tdeff1
if SI1 < td1//HCsize:
    td1 = HCsize*SI1
if 0 < tdeff2 and tdeff2 < 2*td2c:
    td2c = tdeff2//2
if SI2 < td2c:
    td2c = SI2

#print("td1=%d, tdeff1=%d, si1=%d" % (td1, tdeff1, SI1))
#print("td2=%d, tdeff2=%d, si2=%d" % (td2c, tdeff2, SI2))
serfile = serfile[0:td1, 0:td2c]

serfile = serfile.reshape((td1//HCsize, HCsize, td2c))
serfile = numpy.swapaxes(serfile, 0, 1)  # serfile shape is HCsize, td1//2, td2c)

if FnMode == "5" : #State-tppi
    serfile[:, 1::2, :] *= -1 # multiply every other td1 by -1
if FnMode in "4 5" : # States or State-tppi make E/AE
    E  = serfile[0] - 1j*serfile[1]
    AE = serfile[0] + 1j*serfile[1]
elif FnMode == '6':
     E  = serfile[0]
     AE = serfile[1]

exchangeEAE = False
if exchangeEAE:
    E, AE = AE, E

sw2 = float(dat.readacqpar("SW_h", status=True, dimension=1))
sw1 = float(dat.readacqpar("SW_h", status=True, dimension=2))
dw2 = 1.0/sw2
dw1 = 1.0/sw1
# special case of TPPI on dwell with respect to SW
#if FnMode == "3":
#    dw1 /= 2  # if TPPI dw = 0.5 / swh

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
digfilt = dat.getdigfilt()
centerpoint = args.c/dw2/1e6 + digfilt

# create a mesh index matrix
OI = numpy.ones(td2c).reshape((1, td2c))
I = numpy.arange(td2c).reshape((1, td2c)) - centerpoint
OJ = numpy.ones(td1//HCsize).reshape((td1//HCsize, 1))
J = numpy.arange(td1//HCsize).reshape((td1//HCsize, 1))
#2D array (td1/2, td2c) representing the time t for gaussian apodization
Tg = numpy.dot(OJ, I*dw2)
#2D array (td1//HCsize, td2c) representing the time t0 for gaussian apodization along +s (Echo :T0gp) and -s (Antiecho : T0gm)
T0gp = numpy.dot(-J*dw1*args.s, OI)
T0gm = numpy.dot( J*dw1*args.s, OI)
# generates the Gaussian function array (old way not accounting for echo/Antiecho)
#G = numpy.maximum(gauss(args.gb, Tg, T0gp), gauss(args.gb, Tg, T0gm))

# multiply E and AE by gaussian apodization :
E  *= gauss(args.gb, Tg, T0gp)
AE *= gauss(args.gb, Tg, T0gm)

# Lorentzian apodization in t1
#2D array (td1/2, td2c) representing the time t for lorentzian apodization in F1
#Tl = numpy.dot(dw1*J, OI)
#2D array (td1//HCsize, td2c) representing the time t0 for lorentzian apodization
#T0l = numpy.zeros((td1//HCsize, td2c))
# Apodization array
#ApodArray = lorentz(args.lb, Tl, T0l)
#apply apodization (use auto expansion of ApodArray for summed(:, ...) first dimension)
#SUM = summed*ApodArray
# apply the FCOR parameter correction in F1 (multiply first t1 by FCOR)
#fcorF1 = float(dat.readprocpar("FCOR", status=False, dimension=2))
#SUM[:, 0, ...] = SUM[:, 0, ...]*fcorF1

# revert to orginal FnMode
if exchangeEAE:
    E, AE = AE, E

if FnMode in "4 5" : # States or State-tppi from E/AE
    serfile[0] = 0.5*(E+AE)
    serfile[1] = 0.5*1j*(E-AE)
elif FnMode == '6':
     serfile[0] = E
     serfile[1] = AE
if FnMode == "5" : #State-tppi
    serfile[:, 1::2, :] *= -1 # multiply every other td1 by -1

serfile = numpy.swapaxes(serfile, 0, 1).reshape((td1, td2c))

# write back to processing file
rr = serfile.real
ri = serfile.imag
print(rr.shape)
#print(s1.max(), s2.max())
#print(s1.min(), s2.min())

# Apply zero filling according to final size SI1, SI2 from topspin processing parameters
#SI2 = int(dat.readprocpar("SI", False, 1))
#SI1 = int(dat.readprocpar("SI", False, 2))
# note that pad is only available from numpy 1.7.0 : implemented in bruker library
rr = bruker.pad(rr, ((0, SI1-td1), (0, SI2-td2c)), 'constant')
ri = bruker.pad(ri, ((0, SI1-td1), (0, SI2-td2c)), 'constant')
# set all optionnal processing parameters to 0
ProcOptions = {"WDW": ["LB", "GB", "SSB", "TM1", "TM2"],
               "PH_mod": ["PHC0", "PHC1"], "BC_mod": ["BCFW", "COROFFS"],
               "ME_mod": ["NCOEF", "LPBIN", "TDoff"], "FT_mod": ["FTSIZE", "FCOR",
               "STSR", "STSI", "REVERSE"],
               }
for dim in [1, 2]:
    for par in ProcOptions:
        dat.writeprocpar(par, "0", status=True, dimension=dim)
        for opt in ProcOptions[par]:
            dat.writeprocpar(opt, "0", status=True, dimension=dim)

# write 2rr and 2ir files in time/time mode (no ft/ift): 
# SI, STSI and some other parameters are set automatically
dat.writespect2d(rr, "2rr", "tt")
dat.writespect2d(ri, "2ir", "tt")

# write some status processed parameters in procs file so topspin can display 
# and process the data properly
# digital filter is not removed: PKNL must be set to False
dat.writeprocpar("PKNL", "no", status=True)
dat.writeprocpar("WDW", "2", status=True)
dat.writeprocpar("LB", str(-args.gb), status=True)
dat.writeprocpar("GB", "0", status=True)
# unselect apodization for further processing
dat.writeprocpar("WDW", "0", status=False)
