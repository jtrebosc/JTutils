# -*- coding: utf-8 -*-
## does summation of echoes using external python script
import sys
import os
import os.path
import subprocess

import JTutils

dataset = CURDATA()
LB = GETPAR("1 LB")
GB = GETPAR("LB")
s = GETPAR("USERP1")

res = INPUT_DIALOG("processing parameters", 
  """
  please provide  :
     the gaussian broadening (GB) applyied
     the slope for the gaussian center shift (1 for SQSQ or 2 for DQSQ for example).
     
     Should be followed by xf2;xf1 (not xfb as some bug may arise related to F1 apodization)
     """, 
     ["GB=","slope"],[GB,s])
(GB,s) = (res[0],res[1])
PUTPAR("LB",GB)
PUTPAR("USERP1",s)

fulldataPATH = JTutils.fullpath(dataset)
opt_args = " -g %s -l %s -s %s" % (GB,"0",s)

script = JTutils.CpyBin_script("apod2DEAE_.py")
# os.system(" ".join((JTutils.CPYTHON,script,opt_args,fulldataPATH)))
subprocess.call([JTutils.CPYTHON]+[script]+opt_args.split()+[fulldataPATH])    

RE(dataset)
