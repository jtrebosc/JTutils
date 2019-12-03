# -*- coding: utf-8 -*-
import sys
import os
import os.path
import subprocess
import JTutils

# options : 
#     -o [0|1] order is S0/S (0) or S/S0 (1)

optns = ' '.join(sys.argv[1:])

data1d = CURDATA()

fulld1d = JTutils.fullpath(data1d)

script = JTutils.CpyBin("RedFrac1D_.py")
# os.system(" ".join((JTutils.CPYTHON,script,fulld1d,optns," -t 20 ")))
subprocess.call([JTutils.CPYTHON] + [script] + [fulld1d] + optns.split() + ["-t","20"])
RE(data1d)

