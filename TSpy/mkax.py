# -*- coding: utf-8 -*-
import sys
import os
import os.path

# installation directory is relative to current script location
# DIRINST=os.path.dirname(sys.argv[0])+"/../"
def usage():
	MSG("usage mkax first_step step_incr n_step [ax_unit]")

DST=CURDATA()
if len(sys.argv)<4:
    usage()
	EXIT()
if len(sys.argv)==5:
	axunit=sys.argv[4]
else:
	axunit=None

try:
    p1=float(sys.argv[1])
except ValueError:
    MSG("First argument %s must be convertible to a float" % (sys.argv[1] ,))
    usage()
    EXIT()
try:
    p2=float(sys.argv[2])
except ValueError:
    MSG("second argument %s must be convertible to a float" % (sys.argv[2],))
    usage()
    EXIT()
try:
    n=int(sys.argv[3])
except ValueError:
    MSG("Third argument %s must be convertible to an int" % (sys.argv[2],))
    usage()
    EXIT()
axleft=p1-0.5*p2
axright=p1+(n-0.5)*p2

PUTPAR("1s AXLEFT",str(axleft))
PUTPAR("1s AXRIGHT",str(axright))
if axunit:
	PUTPAR("1s AXUNIT",axunit)
RE(DST)
