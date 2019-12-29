# -*- coding: utf-8 -*-
## does summation of echoes using external python script
import sys
import os
import os.path
import subprocess
import JTutils

import os
dataset = CURDATA()
N = str(int(GETPARSTAT("L 22")) - 1)
LB = GETPAR("LB")
GB = GETPAR("USERP1")
s = GETPAR("USERP2")

cycle = float(GETPARSTAT("P 60"))
if (cycle < 1): # P60 is not likely to have stored the cycle time then uses historic calculation
    # historic qcpmg.jt cycle calculation
    D3 = float(GETPARSTAT("D 3"))*1e6
    D6 = float(GETPARSTAT("D 6"))*1e6
    P4 = float(GETPARSTAT("P 4"))
    cycle = 2*(D3+D6)+P4
cycle = str(cycle)

result = INPUT_DIALOG("processing parameters", 
  """please provide the gaussian broadening (GB) applyied
     to each echo, the exponential decay that weight the 
     different echoes and the number of echoes to sum.""", 
     ["GB=","LB=", "N","slope","cycle"],[GB,LB,N,s,cycle])
(GB, LB, N, s, cycle) = (result[0], result[1], result[2], result[3], result[4])
PUTPAR("LB", LB)
PUTPAR("USERP1", GB)
PUTPAR("USERP2", s)

fulldataPATH = JTutils.fullpath(dataset)
opt_args=" -g %s -l %s -n %s -s %s -c %s" % (GB, LB, N, s, cycle)

script = JTutils.CpyBin_script("qcpmgadd2D_.py")
# os.system(" ".join((JTutils.CPYTHON,script,opt_args,fulldataPATH)))
subprocess.call([JTutils.CPYTHON] + [script] + opt_args.split() + [fulldataPATH])    

RE(dataset)
