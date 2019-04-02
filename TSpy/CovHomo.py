# -*- coding: utf-8 -*-
import os
import os.path
import sys
import subprocess

#installation directory is relative to current script location
#add the Library path for importing brukerPAR
DIRINST=os.path.dirname(sys.argv[0])
LIBPATH = DIRINST+"/../CpyLib"
#sys.path.append(PYTHONPATH)
if LIBPATH not in sys.path:
    sys.path.append(LIBPATH)
# where is the external python executable
CPYTHON=os.getenv('CPYTHON',"NotDefined")

import brukerPAR
options=" "
do_xf2=0
if len(sys.argv)>1 :
	if sys.argv[1]=="xf2" : do_xf2=1
	options=" ".join(sys.argv[1:])

data2d=CURDATA()
# special treatment for topspin<3
d2d=data2d[:]
if len(d2d)==5: # for topspin 2-
	d2d[3]="%s/data/%s/nmr" % (d2d[3],d2d[4])
fulld2d="%s/%s/%s/pdata/%s/" % (d2d[3],d2d[0],d2d[1],d2d[2])

dta=brukerPAR.dataset(data2d)
fulld2d=dta.returnprocpath()
fntype=dta.readacqpar("FnTYPE")
if fntype=="2" : 
	dta.writeacqpar("FnTYPE","0" )
XF2()
ABS2()
dta.writeacqpar("FnTYPE",fntype )

if do_xf2==0 :
	script=os.path.expanduser(DIRINST+"/CpyBin/covHomo_.py")
	command=" ".join((CPYTHON,script,options,fulld2d))
	retcode=subprocess.call(command,shell=True)
RE(data2d)
