# -*- coding: utf-8 -*-
import sys
import os
import os.path
import subprocess
import JTutils

if len(sys.argv)>1:
    destproc = sys.argv[1]
else: destproc = "999"

if len(sys.argv)  >2:
    showRES = sys.argv[2]
else: showRES = "y"

data2d = CURDATA()
data1d = data2d[:]
data1d[2] = destproc


fulld2d = JTutils.fullpath(data2d)
fulld1d = JTutils.fullpath(data1d)

RSR("1",procno=destproc,show="n")

JTutils.run_CpyBin_script('stack2D_.py', [fulld2d, fulld1d])

if showRES == 'y':
	NEWWIN()
	RE(data1d)
