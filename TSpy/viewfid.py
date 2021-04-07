# -*- coding: utf-8 -*-
# puts a 2D ser file into the processed spectrum tab without any processing
# If 
import sys
import os


def viewfid(tdeff=False, si=False, rmdigfilt=False, dataset=None):
    from JTutils.CpyLib.brukerPARIO import dataset as bio_dataset
    # it could be interesting to add options hence switch to argparse structure
    # tdeff : keep signal only up to TDEFF
    # si : zero fill data up to SI parameter
    # first process tdeff
    # tdeff : option -t --tdeff
    # if TDEFF=0 or TDEFF>size: no effect, size=size
    # else size=tdeff
    #second process the si option (impact zerofilling/truncation) 
    # si : option -s --si : 
    # if si<size (or tdeff if size=tdeff) : size=si, truncation occurs
    # if si>size : zerofilling occurs

    # Check if acquisition type is traditionnal sampling or Non-uniform sampling.
    # other kind of sampling are not handled (full(points) and projection_spectroscpy)
    if dataset == None:
        dataset = CURDATA()
        RE(dataset)

    FnTYPE = GETPAR("2s FnTYPE")
    if FnTYPE == '0':
        ProcOptions = ["WDW", "PH_mod", "BC_mod", "ME_mod", "FT_mod"]
        dat = bio_dataset(dataset)

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
        optns = [JTutils.fullpath(dataset)]
        if tdeff:
            optns.insert(0,'-t')
        if si:
            optns.insert(0, '-s')
        if rmdigfilt:
            optns.insert(0, '-d')
        JTutils.run_CpyBin_script('viewfid_.py', optns)
    else: 
        MSG("Only Traditionnal(planes) and Non-uniform_sampling FnTYPE are handled by this script.")

if __name__ == '__main__':
    class dummy():
        def __init__(self):
            self.si = False
            self.tdeff = False
            self.rmdigfilt = False
    try : 
        import argparse
        parser  =  argparse.ArgumentParser(description='Transfers a 2D ser file into spectrum tab for time domain observation.')
        parser.add_argument('-t', '--tdeff', help='truncates FID to TDEFF', action='store_true')
        parser.add_argument('-s', '--si', help='Zerofills FID to SI', action='store_true')
        parser.add_argument('-d', '--rmdigfilt', help='Removes digital filter', action='store_true')
        
        args  =  parser.parse_args(sys.argv[1:])
    except ImportError :
        if len(sys.argv) > 1:
            MSG("Argparse module not found!\n Arguments won't be processed")
        args = dummy()
    except SystemExit:
        MSG(""" Script is exiting : either you asked for help or there is an argument error.
        Check console for additional information
        """  + parser.format_help() )
        EXIT()

    dtset = CURDATA()
    viewfid(tdeff=args.tdeff, si=args.si, rmdigfilt=args.rmdigfilt, dataset=dtset)
    RE(dtset)

