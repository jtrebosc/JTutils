#!/usr/bin/python
# -*- coding: utf-8 -*-
# copyright Julien TREBOSC 2012-2013
# check that variable PYTHONPATH points to the right folder for bruker.py library


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
parser.add_argument('-l','--lb',type=float, help='Lorentzian broadening (Hz) applied along F1',default=0)
parser.add_argument('-g','--gb',type=float, help='Gaussian broadening (Hz) applied along t2 centered at t2=s*t1',default=0)
parser.add_argument('-s',type=float, help='s=t2/t1 slope to follow for GB center')
parser.add_argument('infile',help='Full path of the dataset to process')

args=parser.parse_args()
#print bruker.splitprocpath(infile)
dat=bruker.dataset(bruker.splitprocpath(args.infile))

# read ser file and correct automatically for digital filter
serfile=dat.readserc()
(td1,td2c)=serfile.shape
print (td1,td2c)

dw2=1.0/float(dat.readacqpar("SW_h",status=True,dimension=1))
dw1=1.0/float(dat.readacqpar("SW_h",status=True,dimension=2))

# reshape 2D ser file into 3D array of shape (2,td1/2,td2c) and convert to hypercomplex States format 
mode=0
if   (dat.readacqpar("FnMODE",status=True,dimension=2)=='6') : summed=bruker.serc2DEAE2HC(serfile) # echo/antiEcho
elif (dat.readacqpar("FnMODE",status=True,dimension=2)=='5') : summed=bruker.serc2DStatesTppi2HC(serfile)  # States-TPPI
elif (dat.readacqpar("FnMODE",status=True,dimension=2)=='4') : summed=bruker.serc2DStates2HC(serfile) # States
elif (dat.readacqpar("FnMODE",status=True,dimension=2)=='3') : mode=2 # TPPI
elif (dat.readacqpar("FnMODE",status=True,dimension=2)=='2') : mode=2 # QSEQ (obsolete)
elif (dat.readacqpar("FnMODE",status=True,dimension=2)=='1') : mode=2 # QF
elif (dat.readacqpar("FnMODE",status=True,dimension=2)=='0') :  # undefined then reads procpar
	if   (dat.readprocpar("FnMODE",status=False,dimension=2)=='6') : summed=bruker.serc2DEAE2HC(serfile) # echo/antiEcho
	#elif (dat.readprocpar("FnMODE",status=False,dimension=2)=='5') : summed=bruker.ser2DStates2HC(serfile) # States-TPPI
	elif (dat.readprocpar("FnMODE",status=False,dimension=2)=='5') : summed=bruker.serc2DStatesTppi2HC(serfile) # States-TPPI
	elif (dat.readprocpar("FnMODE",status=False,dimension=2)=='4') : summed=bruker.serc2DStates2HC(serfile) # States
	elif (dat.readprocpar("FnMODE",status=False,dimension=2)=='3') : mode=2 # TPPI
	elif (dat.readprocpar("FnMODE",status=False,dimension=2)=='2') : mode=2 # QSEQ (obsolete)
	elif (dat.readprocpar("FnMODE",status=False,dimension=2)=='1') : mode=2 # QF

# create a gaussian apodization function in time domain
# time : exp(-(at)**2) --FT-->  frequency : exp(-(f/2a)**2) with width at half maximum GB = a/pi * 2*sqrt(ln(2))
# hence a=GB*pi/2/sqrt(ln(2))
def gauss(gb,t,t0):
	g=gb*numpy.pi/2.0/numpy.sqrt(numpy.log(2.0))
	return numpy.exp(-(g*(t-t0))**2)
# also define a lorentzian function
def lorentz(lb,t,t0):
	return numpy.exp(-numpy.pi*lb*abs(t-t0))

# create a mesh index matrix
OI=numpy.ones(td2c).reshape((1,td2c))
I=numpy.arange(td2c).reshape((1,td2c))
OJ=numpy.ones(td1/2).reshape((td1/2,1))
J=numpy.arange(td1/2).reshape((td1/2,1))
#2D array (td1/2,td2c) representing the time t for gaussian apodization
Tg=numpy.dot(OJ,I*dw2)
#2D array (td1/2,td2c) representing the time t0 for gaussian apodization along +s (T0gp) and -s (T0gm)
T0gp=numpy.dot(J*dw1*args.s,OI)
T0gm=numpy.dot(-J*dw1*args.s,OI)
#2D array (td1/2,td2c) representing the time t for lorentzian apodization in F1
Tl=numpy.dot(dw1*J,OI)
#2D array (td1/2,td2c) representing the time t0 for lorentzian apodization
T0l=numpy.zeros((td1/2,td2c))
# generates the Gaussian function array
G=numpy.maximum(gauss(args.gb,Tg,T0gp),gauss(args.gb,Tg,T0gm))
# Apodization array
ApodArray=G*lorentz(args.lb,Tl,T0l)

#apply apodization (use auto expansion of ApodArray for summed(:,...) first dimension)
SUM=summed*ApodArray
# apply the FCOR parameter correction in F1 (multiply first t1 by FCOR)
fcorF1=float(dat.readprocpar("FCOR",status=False,dimension=2))
SUM[:,0,...]=SUM[:,0,...]*fcorF1

# ecrit le resultat dans les fichiers 2[ir] :
# separe Re et Im

rr=SUM[0]
ri=SUM[1]

#print s1.max(), s2.max()
#print s1.min(), s2.min()

# Apply zero filling according to final size SI1, SI2 from topspin processing parameters
SI2=int(dat.readprocpar("SI",False,1))
SI1=int(dat.readprocpar("SI",False,2))
rr=numpy.pad(rr,((0,SI1-td1/2),(0,SI2-td2c)),'constant')
ri=numpy.pad(ri,((0,SI1-td1/2),(0,SI2-td2c)),'constant')
# ecrit les fichiers 2rr 2ri 2ir 2ii
dat.writespect2d(rr.real,"2rr","tt")
dat.writespect2d(rr.imag,"2ir","tt")
dat.writespect2d(ri.real,"2ri","tt")
dat.writespect2d(ri.imag,"2ii","tt")

# write some status processed parameters in procs file so topspin can display 
# and process the data properly
dat.writeprocpar("LB","0",status=True)
dat.writeprocpar("LB","0",status=True,dimension=2)
dat.writeprocpar("WDW","0",status=True,dimension=1)
dat.writeprocpar("WDW","0",status=True,dimension=2)
dat.writeprocpar("PKNL","no",status=True)
dat.writeprocpar("PH_mod","0",status=True)
dat.writeprocpar("PH_mod","0",status=True,dimension=2)
dat.writeprocpar("PHC0","0",status=True)
dat.writeprocpar("PHC1","0",status=True)
dat.writeprocpar("PHC0","0",status=True,dimension=2)
dat.writeprocpar("PHC1","0",status=True,dimension=2)
dat.writeprocpar("FTSIZE",str(SI2),status=True)
dat.writeprocpar("FTSIZE",str(SI1),status=True,dimension=2)

# there is the main trick for topspin to understand data for further processing 
# we stored time domain data in 2rr,2ri,2ir,2ii files in States mode 
# therefore we need the status processed data to be (see xfb in bruker procref.pdf manual) :
dat.writeprocpar("FT_mod","2",status=True)              # iqc
dat.writeprocpar("FT_mod","2",status=True,dimension=2)  # iqc
dat.writeprocpar("MC2","3",True,2)                      # States

dat.writeprocpar("AXUNIT","s",status=True)
dat.writeprocpar("AXUNIT","s",status=True,dimension=2)
dat.writeprocpar("AXRIGHT",str(SI2*dw2),status=True)
dat.writeprocpar("AXRIGHT",str(SI1*dw1),status=True,dimension=2)

