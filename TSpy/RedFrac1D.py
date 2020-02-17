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

JTutils.run_CpyBin_script('RedFrac1D_.py', [fulld1d] + optns.split() + ["-t","20"])

RE(data1d)

