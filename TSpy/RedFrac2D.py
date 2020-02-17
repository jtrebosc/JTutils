# -*- coding: utf-8 -*-
import sys
import os
import os.path
import subprocess
import JTutils

# options : 
#     -T [S|S0|F] output is S, S0 or S0-S
#     -o [0|1] order is S0/S (0) or S/S0 (1)

data2d = CURDATA()
optns = ' '.join(sys.argv[1:])

fulld2d = JTutils.fullpath(data2d)

JTutils.run_CpyBin_script('RedFrac2D_.py', [fulld2d] + sys.argv[1:])
RE(data2d)
