# -*- coding: utf-8 -*-
## normalize the noise level to one scan : divide intensity by sqrt(NS)
def norm(ns=None, dataset=None):
    import sys
    import os
    import os.path
    import subprocess

    # if this function is called from imported module then one needs to import TOPSPIN functions
    # so that they are available in the current namespace
    from TopCmds import CURDATA, GETPAR, GETPARSTAT, PUTPAR, RE, INPUT_DIALOG, MSG

    if dataset == None:
        dataset = CURDATA()
    # process the arguments that are handled by this script
    if ns == None:
        ns = GETPARSTAT("NS")

    # installation directory is relative to current script location
    DIRINST = os.path.dirname(sys.argv[0])+"/../"
    # where is the external python executable
    CPYTHON = os.getenv('CPYTHON', "NotDefined")
    if "python" not in CPYTHON:
            MSG("CPYTHON environment not defined")
            EXIT()
    # MSG(CPYTHON)

    # special treatment for topspin<3
    def fullpath(dataset):
        dat = dataset[:] # make a copy because I don't want to modify the original array
        if len(dat) ==5: # for topspin 2-
                dat[3] = "%s/data/%s/nmr" % (dat[3], dat[4])
        fulldata = "%s/%s/%s/pdata/%s/" % (dat[3], dat[0], dat[1], dat[2])
        return fulldata
    fulldataPATH = fullpath(dataset)

    opt_args = "--ns %s " % (ns,)


    script = os.path.expanduser(DIRINST+"/CpyBin/norm_noise_per_scan_.py")
    # os.system(" ".join((CPYTHON, script, opt_args, fulldataPATH)))
    print([CPYTHON]+[script]+opt_args.split()+[fulldataPATH])    
    subprocess.call([CPYTHON]+[script]+opt_args.split()+[fulldataPATH])    

if __name__ == '__main__':
    class dummy():
        def __init__(self):
            self.ns = 0

    try : 
        import argparse
        parser  =  argparse.ArgumentParser(description='normalize the noise level to one scan : divide intensity by sqrt(NS).')
        parser.add_argument('--ns', help='Number of scan used for normalization. Could be float in special cases', default=None)
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
    dataset = CURDATA()
    norm(ns=args.ns, dataset=dataset)
    RE(dataset)
