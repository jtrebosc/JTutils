# set all optionnal processing parameters to 0
import sys
import os

DIRINST = os.path.dirname(sys.argv[0]) 
LIBPATH = DIRINST+ "/../CpyLib"
if LIBPATH not in sys.path:
    sys.path.append(LIBPATH)
from brukerPAR import dataset

ProcOptions = ["WDW", "PH_mod", "BC_mod", "ME_mod", "FT_mod"]
dat = dataset(CURDATA())

Stored=[{},{}]
for dim in [0, 1]:
    for par in ProcOptions:
        Stored[dim][par]=GETPAR("%d %s" % (dim+1,par))
#        MSG("%d %s" % (dim+1,par)+" is "+Stored[dim][par])
for dim in [0, 1]:
    for par in ProcOptions:
        dat.writeprocpar(par, "0", dimension=2-dim, status=False)
        # PUTPAR("%d %s" % (dim+1,par),"0")
print Stored

XTRF()

for dim in [0, 1]:
    for par in ProcOptions:
        dat.writeprocpar(par, Stored[dim][par], dimension=2-dim, status=False)

