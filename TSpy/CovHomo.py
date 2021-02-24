# -*- coding: utf-8 -*-
import os
import os.path
import sys
import subprocess

import JTutils
import JTutils.CpyLib.brukerPARIO as brukerPARIO

options = []
do_xf2 = 0
if len(sys.argv)>1 :
	if sys.argv[1] == "xf2" : do_xf2 = 1
	options += sys.argv[1:]

data2d = CURDATA()
fulld2d = JTutils.fullpath(data2d)

dta = brukerPARIO.dataset(data2d)
fulld2d = dta.returnprocpath()
fntype = dta.readacqpar("FnTYPE")
if fntype == "2" : 
	dta.writeacqpar("FnTYPE", "0")
XF2()
ABS2()
dta.writeacqpar("FnTYPE",fntype )

if do_xf2 == 0 :
        retcode = JTutils.run_CpyBin_script('CovHomo_.py', options+[fulld2d])
RE(data2d)
