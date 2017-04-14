# -*- coding: utf-8 -*-
## does summation of echoes using external python script
import sys
import os
import os.path
import subprocess

"""
import argparse

parser = argparse.ArgumentParser(description='Add echoes in a qcpmg bruker experiment')
parser.add_argument('-g', '--gb', type=float,  help='Gaussian broadening applied to each echo', default=0)
parser.add_argument('-n', type=int,  help='Number of echo to sum')
parser.add_argument('-c', type=float,  help='qcpmg cycle in us')
parser.add_argument('infile', help='Full path of the dataset to process')
"""

# installation directory is relative to current script location
DIRINST = os.path.dirname(sys.argv[0])+"/../"
# where is the external python executable
CPYTHON = os.getenv('CPYTHON', "NotDefined")
if "python" not in CPYTHON:
		MSG("CPYTHON environment not defined")
		EXIT()
# MSG(CPYTHON)


dataset = CURDATA()
N = str(1+int(GETPARSTAT("L 22")))
GB = GETPAR("USERP1")
cycle = float(GETPARSTAT("P 60"))
if cycle < 1:  
    # P60 is not likely to have stored the cycle time then uses historic calculation
    D3 = float(GETPARSTAT("D 3"))*1e6
    D6 = float(GETPARSTAT("D 6"))*1e6
    P4 = float(GETPARSTAT("P 4"))
    cycle = 2*(D3+D6)+P4
cycle = str(cycle)
result = INPUT_DIALOG("processing parameters", 
  """please provide the gaussian broadening (GB) applyied
     to each echo, the exponential decay that weight the 
     different echoes and the number of echoes to sum.""", 
     ["GB=", "N","cycle time (us)"],[GB, N, cycle])
(GB, N, cycle) = (result[0], result[1], result[2])
PUTPAR("USERP1", GB)

# special treatment for topspin<3
def fullpath(dataset):
	dat=dataset[:] # make a copy because I don't want to modify the original array
	if len(dat) == 5: # for topspin 2-
	        dat[3] = "%s/data/%s/nmr" % (dat[3], dat[4])
	fulldata = "%s/%s/%s/pdata/%s/" % (dat[3], dat[0], dat[1], dat[2])
	return fulldata
fulldataPATH=fullpath(dataset)

opt_args = " -g %s -n %s -c %s" % (GB, N, cycle)

script = os.path.expanduser(DIRINST+"/CpyBin/qcpmgapod_.py")
# os.system(" ".join((CPYTHON, script, opt_args, fulldataPATH)))
subprocess.call([CPYTHON] + [script] + opt_args.split() + [fulldataPATH])    

RE(dataset)
