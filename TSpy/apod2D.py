# -*- coding: utf-8 -*-
## does summation of echoes using external python script
import sys
import os
import os.path
import subprocess

import JTutils

dataset = CURDATA()
#LB = GETPAR("1 LB")
GB = GETPAR("LB")
s = GETPAR("USERP1")
c = GETPAR("USERP2")
e = "0"
res = INPUT_DIALOG("processing parameters", 
  """
  please provide  :
     the gaussian broadening (GB) applyied
     the slope for the gaussian center shift (1 for SQSQ or 2 for DQSQ for example).
     the center of gaussian or lorentzian in time excluding digital filter delay
     whether you only want to apodize the echo only (0=both, 1=echo Only)
     """, 
     ["GB=", "slope=", "center (usec)=", "echo only"], [GB, s, c, e])
(GB, s, c, e) = (res[0], res[1], res[2], int(res[3]))
PUTPAR("LB", GB)
PUTPAR("USERP1", s)
PUTPAR("USERP2", c)

fulldataPATH = JTutils.fullpath(dataset)

if e:
	echoOnly = '-e'
else:
  echoOnly = ''
opt_args = " -g %s -s %s -c %s %s " % (GB, s, c, echoOnly)

script = JTutils.CpyBin_script("apod2D_.py")
# os.system(" ".join((JTutils.CPYTHON,script,opt_args,fulldataPATH)))
subprocess.call([JTutils.CPYTHON] + [script] + opt_args.split() + [fulldataPATH])
RE(dataset)
