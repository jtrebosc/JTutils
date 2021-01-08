# -*- coding: utf-8 -*-
# set all optionnal processing parameters to 0
import sys
import os

from JTutils.CpyLib.brukerPAR import dataset
current_expno = CURDATA()

FnTYPE = GETPAR("2s FnTYPE")
if FnTYPE == '0':
    ProcOptions = ["WDW", "PH_mod", "BC_mod", "ME_mod", "FT_mod"]
    dat = dataset(current_expno)

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

if FnTYPE == '2':
    import JTutils
    JTutils.run_CpyBin_script('viewfid_.py', [])

RE(current_expno)
