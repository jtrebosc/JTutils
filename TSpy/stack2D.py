# -*- coding: utf-8 -*-
import sys
import os
import os.path
import subprocess

#installation directory is relative to current script location
DIRINST=os.path.dirname(sys.argv[0])+"/../"
# where is the external python executable
CPYTHON=os.getenv('CPYTHON')
if not CPYTHON:
	MSG("CPYTHON variable cannot be found")
	EXIT()
if len(sys.argv)>1:
	destproc=sys.argv[1]
else:destproc="999"

if len(sys.argv)>2:
	showRES=sys.argv[2]
else:showRES="y"

data2d=CURDATA()
data1d=data2d[:]
data1d[2]=destproc

# special treatment for topspin<3
d2d=data2d[:]
d1d=data1d[:]
if len(d2d)==5: # for topspin 2-
	d2d[3]="%s/data/%s/nmr" % (d2d[3],d2d[4])
	d1d[3]=d2d[3]

fulld2d="%s/%s/%s/pdata/%s/" % (d2d[3],d2d[0],d2d[1],d2d[2])
fulld1d="%s/%s/%s/pdata/%s/" % (d1d[3],d1d[0],d1d[1],d1d[2])

RSR("1",procno=destproc,show="n")

script=os.path.expanduser(DIRINST+"/CpyBin/stack2D_.py")
print " ".join((CPYTHON,script,fulld2d,fulld1d))
# os.system(" ".join((CPYTHON,script,fulld2d,fulld1d)))
subprocess.call([CPYTHON]+[script]+[fulld2d]+[fulld1d])    

if showRES=='y':
	NEWWIN()
	RE(data1d)
