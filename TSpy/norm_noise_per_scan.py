# -*- coding: utf-8 -*-
## normalize the noise level to one scan : divide intensity by sqrt(NS)
def norm(ns=None, dataset=None):
    import sys
    import os
    import os.path
    import subprocess
    import JTutils

    # if this function is called from imported module then one needs to import TOPSPIN functions
    # so that they are available in the current namespace
    from TopCmds import CURDATA, GETPAR, GETPARSTAT, PUTPAR, RE, INPUT_DIALOG, MSG

    if dataset == None:
        dataset = CURDATA()
    # process the arguments that are handled by this script
    if ns == None:
        ns = GETPARSTAT("NS")

    fulldataPATH = JTutils.fullpath(dataset)

    opt_args = ["--ns", str(ns)]

    JTutils.run_CpyBin_script('norm_noise_per_scan_.py', opt_args + [fulldataPATH])

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
