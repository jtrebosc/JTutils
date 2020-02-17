#!/usr/bin/python
# -*- coding: UTF-8 -*-
# copyright Julien TREBOSC 2012-2013
from __future__ import division

import numpy
import sys
import bruker
import math
# gestion des arguments
import argparse

try:
    from multiprocessing import Pool
except:
    from processing import Pool



parser = argparse.ArgumentParser(description='Covariance calculation')
parser.add_argument('-r','--addref',action='store_true', help='Add dummy reference diagonal spectrum')
parser.add_argument('-n','--nrowref',type=int, help='Calculate the reference signal on the nrowref first rows',default=10)
parser.add_argument('-b','--reflb',type=float, help='Line broadening of reference diagonal peaks',default=0)
parser.add_argument('-w','--refW',type=float, help='Weight of reference diagonal peaks',default=5)
parser.add_argument('-p0','--refPh0',type=float, help='Zero order phase of reference diagonal peaks',default=0)
parser.add_argument('-p1','--refPh1',type=float, help='First order phase of reference diagonal peaks',default=0)
parser.add_argument('-s','--slope',type=float, help='slope of diagonal peaks : 1 for SQ-SQ or 2 for DQ-SQ',default=1)
#parser.add_argument('-d','--extradelay',type=float, help='Extra delay in addition to D0 for initial t1 (in us)',default=0.0)
parser.add_argument('infile',help='Full path of the dataset to process')
args=parser.parse_args()
LB=args.reflb
refWeight=args.refW
nrowref=args.nrowref
ADDREF=args.addref
slope=args.slope
PHI0=-args.refPh0/180*numpy.pi
PHC1=-args.refPh1
#print(bruker.splitprocpath(infile))
dat=bruker.dataset(bruker.splitprocpath(args.infile))

# FnMODE=0 undefined, 1 QF, 2 QSEQ, 3 TPPI, 4 States, 5 States-TPPI, 6 Echo-Antiecho
MODEflag=dat.readacqpar("FnMODE",dimension=2)

DWf1=1e-6*float(dat.readacqpar("INF 1",dimension=1))
#print(DWf1)
TDf1=int(dat.readacqpar("TD",dimension=2))
# if states/states-ttpi then TDf1 must be even else remove one row
if MODEflag=="4" or MODEflag=="5" :
	if TDf1%2==1 : TDf1-=1
#D0=float(dat.readacqpar("D 0",dimension=1))
si2=int(dat.readprocpar("FTSIZE",dimension=1))
if (si2==0):
	print('F2 fourier transform not performed yet : exiting...')
	sys.exit()
swh2=float(dat.readacqpar("SW_h",dimension=1))
HzpPTf2=swh2/si2
sistart=si2//2-int(dat.readprocpar("STSR",dimension=1))
#init_t1=D0+args.extradelay/1e6
#print(init_t1)


# NUSlist list of acquired complex rows starting from 0

spect2D=dat.readspect2d("2rr")

#dat.writespect2d(spect2D,"2rr")
#exit()
(si1,si2)=spect2D.shape
if TDf1<si1:
	spect2D=spect2D[0:TDf1][:]
(td1,si2)=spect2D.shape
print(td1,si2)

# FnTYPE=0 (traditionnal), 1 (full point ???), 2 (NUS)
NUSflag=dat.readacqpar("FnTYPE",dimension=1)
NUSlist=[]
print("NUSFLAG is %s" % (NUSflag))
if NUSflag=="2":
	NUSfile=dat.returnacqpath()+"nuslist"
	list=open(NUSfile,"r").read().strip("\n").split()
# la nuslist a des index de 0 à td1//2-1
	NUSlist=[(int(list[i])) for i in range(td1//2)]
else :
	NUSlist=range(td1//2)

# Traitement de States et states tppi pour l'instant
if MODEflag=="4" or MODEflag=="5" :
	td1=(td1//2)*2
	spect2D=spect2D.reshape(td1//2,2,si2)
	spect2D=spect2D.swapaxes(0,1)
	NUSlist=NUSlist[0:td1//2]
	# now spect2D[C=0 or S=1][td1//2][si2]
else:
	NUSlist=NUSlist[0:td1]
	
print("this is nuslist:")
print(NUSlist)

# calculate reorder of the rows in case of shuffled NUS acquisition
if NUSflag=="2":
	NUSsorted=sorted(NUSlist)
	NUSsortedIndex=[]
	for i in NUSsorted:
		NUSsortedIndex.append(NUSlist.index(i))
	print('NUSsortedIndex 2 :')
else :
	NUSsortedIndex=range(td1//2)
	print('NUSsortedIndex 1 :')
print(NUSsortedIndex)

# correct for States-TPPI mode
if MODEflag=="5" :
	for i in range(len(NUSlist)):
		if (NUSlist[i])%2:
			spect2D[0][i][:]=-spect2D[0][i][:]
			spect2D[1][i][:]=-spect2D[1][i][:]
		
# make a reference row from nrowref first rows (sorted by ascending index)
a=spect2D[0][NUSsortedIndex[0]][:]
ref=numpy.sqrt(spect2D[0][NUSsortedIndex[0]][:]**2+spect2D[1][NUSsortedIndex[0]][:]**2)
for i in range(1,nrowref):
	ref+=numpy.sqrt(spect2D[0][NUSsortedIndex[i]][:]**2+spect2D[1][NUSsortedIndex[i]][:]**2)


def makeRef(ref,NUSlist):
	Iarray=numpy.reshape(slope*2*numpy.pi*(numpy.array(NUSlist)*DWf1+PHC1/360.0*DWf1)*HzpPTf2,(1,len(NUSlist)))
	Jarray=numpy.reshape(numpy.arange(ref.size)-sistart,(1,ref.size))
	expdecarray=numpy.reshape(numpy.exp(-numpy.array(NUSlist)*DWf1*LB),(1,len(NUSlist)))
	ref=ref.reshape((1,ref.size))
# apply zeroth order correction + pivot point of first order correction
	PhCorrection=PHI0+0.5*numpy.pi*PHC1/180.0
	REFc=numpy.dot(expdecarray.T,ref)*numpy.cos(numpy.dot(Iarray.T,Jarray)+PhCorrection)
	REFs=numpy.dot(expdecarray.T,ref)*numpy.sin(-numpy.dot(Iarray.T,Jarray)-PhCorrection)
	return (REFc,REFs)


def testREF(Zfill1=1024):
	# test : write back the ref
	# OK only if not using NUS
	REF=numpy.zeros((2,Zfill1//2,si2))
	(REF[0],REF[1])=makeRef(ref,range(Zfill1//2))
	# correct back to States-TPPI mode
	if MODEflag=="5" :
		REF[0][1:Zfill1//2:2]*=-1.0
		REF[1][1:Zfill1//2:2]*=-1.0
	REF=REF.swapaxes(0,1)
	# attention il faut copier la vue du tableau REF dans un nouveau tableau pour pouvoir faire resize
	REF=REF.reshape(Zfill1,si2).copy()
	dat.writespect2d(REF,"2rr")
	sys.exit()
#uncomment to test for reference generation
#testREF(int(dat.readprocpar("SI",dimension=2)))

def calculateCov(InputMatrix):
	(U,S,V)=numpy.linalg.svd(InputMatrix,full_matrices=False)
	print("SVD made----")
	return numpy.dot(V.T,numpy.dot(numpy.diag(S),V))
#	print("COV made----")
#	return OuputMatrix.copy()


if ADDREF:
	(REFc,REFs)=makeRef(ref,NUSlist)
	print("REF made----")
	Sc=spect2D[0]+refWeight*REFc
	Ss=spect2D[1]+refWeight*REFs

	calculateList=[REFc,REFs,Sc,Ss]
	pool = Pool(processes=4)
	(covRefc,covRefs,covSc,covSs)=pool.map(calculateCov, calculateList)

	spect2D=1*numpy.sqrt(si2)*(covSc+covSs-refWeight*(covRefc+covRefs))
else:
	Sc=spect2D[0]
	Ss=spect2D[1]

	calculateList=[Sc,Ss]
	pool = Pool(processes=2)
	(covSc,covSs)=pool.map(calculateCov, calculateList)

	spect2D=1*numpy.sqrt(si2)*(covSc+covSs)



dat.writespect2d(spect2D,"2rr")

# reste a copier SW_p FT_mod FTSIZE AXUNIT AXRIGHT YMAX OFFSET
# pour faire croire a TOPSPIN que la FT a ete faite
for i in ['SW_p','FT_mod','FTSIZE','AXUNIT','AXRIGHT','OFFSET']:
	tmp=dat.readprocpar(i,dimension=1)
	dat.writeprocpar(i,tmp,dimension=2)
	print(i + " is " + tmp)
#stsr,stsi, si1, 
