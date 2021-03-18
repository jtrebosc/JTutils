# -*- coding: utf-8 -*-
# puts a 2D ser file into the processed spectrum tab without any processing
# If 
import sys
import os

from JTutils.CpyLib.brukerPARIO import dataset
current_expno = CURDATA()

# Check if acquisition type is traditionnal sampling or Non-uniform sampling.
# other kind of sampling are not handled (full(points) and projection_spectroscpy)

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
#    print Stored

    XTRF()

    for dim in [0, 1]:
        for par in ProcOptions:
            dat.writeprocpar(par, Stored[dim][par], dimension=2-dim, status=False)

elif FnTYPE == '2':
    import JTutils
    fulldataPATH = JTutils.fullpath(current_expno)
    JTutils.run_CpyBin_script('viewfid_.py', [fulldataPATH])
else: 
    MSG("Only Traditionnal(planes) and Non-uniform_sampling FnTYPE are handled by this script.")
RE(current_expno)
