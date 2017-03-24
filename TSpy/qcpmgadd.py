# -*- coding: utf-8 -*-
## does summation of echoes using external python script
import sys
import os
import os.path

"""
import argparse

parser = argparse.ArgumentParser(description='Add echoes in a qcpmg bruker experiment')
parser.add_argument('-l','--lb',type=float, help='Lorentzian broadening applied to the decaying echo',default=0)
parser.add_argument('-g','--gb',type=float, help='Gaussian broadening applied to each echo',default=0)
parser.add_argument('-n',type=int, help='Number of echo to sum')
parser.add_argument('-c',type=float, help='qcpmg cycle in us')
parser.add_argument('infile',help='Full path of the dataset to process')
"""

#installation directory is relative to current script location
DIRINST=os.path.dirname(sys.argv[0])+"/../"
# where is the external python executable
CPYTHON=os.getenv('CPYTHON')
if "python" not in CPYTHON:
		MSG("CPYTHON environment not defined")
		EXIT()
#MSG(CPYTHON)


dataset=CURDATA()
N=str(1+int(GETPARSTAT("L 22")))
LB=GETPAR("LB")
GB=GETPAR("USERP1")
cycle=float(GETPARSTAT("P 60"))
if cycle < 1: # P60 is not likely to have stored the cycle time then uses historic calculation
    # historic qcpmg.jt cycle calculation
    D3=float(GETPARSTAT("D 3"))*1e6
    D6=float(GETPARSTAT("D 6"))*1e6
    P4=float(GETPARSTAT("P 4"))
    cycle=2*(D3+D6)+P4
cycle=str(cycle)
result=INPUT_DIALOG("processing parameters", 
  """please provide the gaussian broadening (GB) applyied
     to each echo, the exponential decay that weight the 
     different echoes and the number of echoes to sum.""", 
     ["GB=","LB=", "N","cycle time (us)"],[GB,LB,N,cycle])
(GB,LB,N,cycle)=(result[0],result[1],result[2],result[3])
PUTPAR("LB",LB)
PUTPAR("USERP1",GB)

# special treatment for topspin<3
def fullpath(dataset):
	dat=dataset[:] # make a copy because I don't want to modify the original array
	if len(dat)==5: # for topspin 2-
	        dat[3]="%s/data/%s/nmr" % (dat[3],dat[4])
	fulldata="%s/%s/%s/pdata/%s/" % (dat[3],dat[0],dat[1],dat[2])
	return fulldata
fulldataPATH=fullpath(dataset)

opt_args=" -g %s -l %s -n %s -c %s" % (GB,LB,N,cycle)

script=os.path.expanduser(DIRINST+"/CpyBin/qcpmgadd_.py")
os.system(" ".join((CPYTHON,script,opt_args,fulldataPATH)))
RE(dataset)
