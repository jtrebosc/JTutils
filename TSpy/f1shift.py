# -*- coding: utf-8 -*-
## call an external python script that does a round shift in F1 dimension
import sys
import os
import os.path
import subprocess
import JTutils

description = """ 
Call an external python script that does a round shift in F1 dimension
"""



# TODO deal with arguments with argparse (see scalef1shear)
if len(sys.argv) > 1:
	N = sys.argv[1]
else: 
    N = "0"

dataset = CURDATA()


if N == "0":
	N = GETPAR("USERP3")
	result = INPUT_DIALOG("Shift 2D in F1", 
	  """please provide the number of points to be shifted.""", 
      ["N"], [N])
	N = result[0]
PUTPAR("USERP3", N)

fulldataPATH = JTutils.fullpath(dataset)

opt_args = ["-n", str(N)]

script = JTutils.CpyBin_script("f1shift_.py")
#os.system(" ".join((JTutils.CPYTHON,script,opt_args,fulldataPATH)))
subprocess.call([JTutils.CPYTHON] + [script] + opt_args + [fulldataPATH])    

RE(dataset)
