# -*- coding: utf-8 -*-
## normalize the noise level to one scan : divide intensity by sqrt(NS)
def norm(args):
    import sys
    import os
    import os.path
    import subprocess
    # if this function is called from imported module then one needs to import TOPSPIN functions
    # so that they are available in the current namespace
    from TopCmds import CURDATA, GETPAR, GETPARSTAT, PUTPAR, RE, INPUT_DIALOG, MSG

# whether CURDATA should be called here or specific dataset should be provided as argument is not clear
    dataset = CURDATA()
    RE(dataset)
    # process the arguments that are handled by this script
    if args.ns:
        ns = args.ns
    else:
        ns = int(GETPARSTAT("NS"))

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

    opt_args = "--ns %f"%(ns,)


    script = os.path.expanduser(DIRINST+"/CpyBin/norm_noise_per_scan_.py")
    # os.system(" ".join((CPYTHON, script, opt_args, fulldataPATH)))
    print([CPYTHON]+[script]+opt_args.split()+[fulldataPATH])    
    subprocess.call([CPYTHON]+[script]+opt_args.split()+[fulldataPATH])    

    RE(dataset)

if __name__ == '__main__':
    class dummy():
        def __init__(self):
            self.ns = 0

    try : 
        import argparse
        parser  =  argparse.ArgumentParser(description='normalize the noise level to one scan : divide intensity by sqrt(NS).')
        parser.add_argument('--ns', type = float, help='Number of scan used for normalization. Could be float in special cases', default=0)
        args  =  parser.parse_args()
    except Exception as ex:
        if len(sys.argv) > 1:
            MSG("Argparse module not found!\n Arguments won't be processed")
        args = dummy()
    
    dataset = CURDATA()
    norm(args)
    RE(dataset)
