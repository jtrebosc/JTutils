# -*- coding: utf-8 -*-
import sys
import os
import os.path
import subprocess

#installation directory is relative to current script location
DIRINST=os.path.dirname(sys.argv[0])+"/../"
# where is the external python executable
CPYTHON=os.getenv('CPYTHON',"NotDefined")

# options : 
#     -T [S|S0|F] output is S, S0 or S0-S
#     -o [0|1] order is S0/S (0) or S/S0 (1)

data2d=CURDATA()
optns=' '.join(sys.argv[1:])

# special treatment for topspin<3
d2d=data2d[:]
if len(d2d)==5: # for topspin 2-
	d2d[3]="%s/data/%s/nmr" % (d2d[3],d2d[4])

fulld2d="%s/%s/%s/pdata/%s/" % (d2d[3],d2d[0],d2d[1],d2d[2])

script=DIRINST+"CpyBin/RedFrac2D_.py"
os.system(" ".join((CPYTHON,script,fulld2d,optns)))
subprocess.call([CPYTHON]+[script]+[fulld2d]+sys.argv[1:])
RE(data2d)
