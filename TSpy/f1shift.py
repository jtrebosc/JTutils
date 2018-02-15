# -*- coding: utf-8 -*-
## call an external python script that does a round shift in F1 dimension
import sys
import os
import os.path
import subprocess

description = """ 
Call an external python script that does a round shift in F1 dimension
"""

#installation directory is relative to current script location
DIRINST = os.path.dirname(sys.argv[0]) + "/../"
# where is the external python executable
CPYTHON = os.getenv('CPYTHON', "NotDefined")
if "python" not in CPYTHON:
		MSG("CPYTHON environment not defined")
		EXIT()
#MSG(CPYTHON)


# TODO deal with arguments with argparse (see scalef1shear)
if len(sys.argv) > 1:
	N = sys.argv[1]
else: 
    N = "0"

dataset=CURDATA()


if N == "0":
	N = GETPAR("USERP3")
	result = INPUT_DIALOG("Shift 2D in F1", 
	  """please provide the number of points to be shifted.""", 
      ["N"], [N])
	N = result[0]
PUTPAR("USERP3", N)

# special treatment for topspin<3
def fullpath(dataset):
	dat = dataset[:] # make a copy because I don't want to modify the original array
	if len(dat) == 5: # for topspin 2-
	        dat[3] = "%s/data/%s/nmr" % (dat[3], dat[4])
	fulldata = "%s/%s/%s/pdata/%s/" % (dat[3], dat[0], dat[1], dat[2])
	return fulldata
fulldataPATH = fullpath(dataset)

opt_args = " -n %s " % (N,)

script = os.path.expanduser(DIRINST + "/CpyBin/f1shift_.py")
#os.system(" ".join((CPYTHON,script,opt_args,fulldataPATH)))
subprocess.call([CPYTHON] + [script] + opt_args.split()+ [fulldataPATH])    

RE(dataset)
