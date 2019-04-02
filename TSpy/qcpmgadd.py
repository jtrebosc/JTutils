# -*- coding: utf-8 -*-
## does summation of echoes using external python script
## new writing in a module like fashion in order to be able to call it from another python script
def addechoes(args):
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
    if args.lb : 
        LB = args.lb
    else:
         LB = GETPAR("LB")

    if args.gb:
        GB = args.gb
    else :
         GB = GETPAR("USERP1")

    if args.c:
        cycle = args.c
    else:
        cycle = float(GETPARSTAT("P 60"))
        if cycle < 1:  
            # P60 is not likely to have stored the cycle time then uses historic calculation
            D3 = float(GETPARSTAT("D 3"))*1e6
            D6 = float(GETPARSTAT("D 6"))*1e6
            P4 = float(GETPARSTAT("P 4"))
            cycle = 2*(D3+D6) + P4
    cycle = str(cycle)

    if args.n: 
        N = args.n 
    else:
        N = str(1+int(GETPARSTAT("L 22")))
            
    # installation directory is relative to current script location
    DIRINST = os.path.dirname(sys.argv[0])+"/../"
    # where is the external python executable
    CPYTHON = os.getenv('CPYTHON', "NotDefined")
    if "python" not in CPYTHON:
            MSG("CPYTHON environment not defined")
            EXIT()
    # MSG(CPYTHON)

    if not args.noDialog:
        result = INPUT_DIALOG("processing parameters", 
          """please provide the gaussian broadening (GB) applyied
             to each echo, the exponential decay that weight the 
             different echoes and the number of echoes to sum.""", 
             ["GB = ", "LB=", "N", "cycle time (us)"], [GB, LB, N, cycle])
        (GB, LB, N, cycle) = (result[0], result[1], result[2], result[3])
    PUTPAR("LB", LB)
    PUTPAR("USERP1", GB)

    # special treatment for topspin<3
    def fullpath(dataset):
        dat = dataset[:] # make a copy because I don't want to modify the original array
        if len(dat) ==5: # for topspin 2-
                dat[3] = "%s/data/%s/nmr" % (dat[3], dat[4])
        fulldata = "%s/%s/%s/pdata/%s/" % (dat[3], dat[0], dat[1], dat[2])
        return fulldata
    fulldataPATH = fullpath(dataset)

    opt_args = " -g %s -l %s -n %s -c %s " % (GB, LB, N, cycle)
    if args.norm_noise:
        opt_args += "--norm_noise"


    script = os.path.expanduser(DIRINST+"/CpyBin/qcpmgadd_.py")
    # os.system(" ".join((CPYTHON, script, opt_args, fulldataPATH)))
    print([CPYTHON]+[script]+opt_args.split()+[fulldataPATH])    
    subprocess.call([CPYTHON]+[script]+opt_args.split()+[fulldataPATH])    

    RE(dataset)

if __name__ == '__main__':
    try : 
        import argparse
        parser  =  argparse.ArgumentParser(description='Add echoes in a qcpmg bruker experiment')
        parser.add_argument('-l', '--lb', type = str, help='Lorentzian broadening applied to the decaying echo', default=0)
        parser.add_argument('-g', '--gb', type = str, help='Gaussian broadening applied to each echo', default=0)
        parser.add_argument('-n', type = str, help='Number of echo to sum', default=0)
        parser.add_argument('-c', type = str, help='qcpmg cycle in us', default=0)
        parser.add_argument('--noDialog',action='store_true', help='Do not show dialog : use default or provided optional arguments')
        parser.add_argument('--norm_noise',action='store_true', help='Normalize noise as function of number of echoes added.')
        parser.add_argument('infile', help = 'Full path of the dataset to process')
        args  =  parser.parse_args(sys.argv)
    except Exception as ex:
        if len(sys.argv) > 1:
            MSG("Argparse module not found!\n Arguments won't be processed")
        class dummy():
            def __init__(self):
                self.lb = 0
                self.gb = 0
                self.c = 0
                self.n = 0
                self.noDialog = False
                self.norm_noise = False
        args = dummy()
    dataset = CURDATA()
    addechoes(args)
