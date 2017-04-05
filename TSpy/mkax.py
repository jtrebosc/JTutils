# -*- coding: utf-8 -*-
import sys
import os
import os.path

# installation directory is relative to current script location
# DIRINST=os.path.dirname(sys.argv[0])+"/../"

DST=CURDATA()
if len(sys.argv)<4:
	MSG("usage mkax first_step step_incr n_step [ax_unit]")
	EXIT()
if len(sys.argv)==5:
	axunit=sys.argv[4]
else:
	axunit=None

p1=float(sys.argv[1])
p2=float(sys.argv[2])
n=float(sys.argv[3])
axleft=p1-0.5*p2
axright=p1+(n-0.5)*p2

PUTPAR("1s AXLEFT",str(axleft))
PUTPAR("1s AXRIGHT",str(axright))
if axunit:
	PUTPAR("1s AXUNIT",axunit)
RE(DST)
