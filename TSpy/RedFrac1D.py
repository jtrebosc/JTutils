# -*- coding: utf-8 -*-
import sys
import os
import os.path

#installation directory is relative to current script location
DIRINST=os.path.dirname(sys.argv[0])+"/../"
# where is the external python executable
CPYTHON=os.getenv('CPYTHON')


# options : 
#     -o [0|1] order is S0/S (0) or S/S0 (1)

optns=' '.join(sys.argv[1:])

data1d=CURDATA()

# special treatment for topspin<3
d1d=data1d[:]
if len(d1d)==5: # for topspin 2-
	d1d[3]="%s/data/%s/nmr" % (d1d[3],d1d[4])

fulld1d="%s/%s/%s/pdata/%s/" % (d1d[3],d1d[0],d1d[1],d1d[2])

script=DIRINST+"CpyBin/RedFrac1D_.py"
os.system(" ".join((CPYTHON,script,fulld1d,optns," -t 20 ")))

RE(data1d)

