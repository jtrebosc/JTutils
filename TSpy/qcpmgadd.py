# -*- coding: utf-8 -*-
## does summation of echoes using external python script
## new writing in a module like fashion in order to be able to call it from another python script
def add_echoes(args):
    """
    This function applies a gaussian apodization to each echo of a cpmg acquisition
    that used qcpmg.jt pulse sequence by calling an external python program.
    All echoes are added together with a weight using exponential multiplication 
    corrresponding to a spiklet broadening LB (Hz)
    It may be used for other pulse sequences.
    It takes one parameter args that is a class with the mandatory following 
    variables:
        args.gb
        args.lb
        args.n
        args.c
        args.echo_position
        args.norm_noise
        args.e
        args.o
    If a variable is set to None a default value is chosen
     gb:            gaussian broadening (Hz) (default value stored in USERP1)
     lb:            lorentzian broadening for echo weighting
     n:             number of echoes to add (value stored in USERP3)
                    invalid number or 0 defaults to L22+1
     echo_position: Position of echo with respect to start of FID (not including digital filter)
          Position is stored in USERP1, it defaults to D3+D6. 
          The value stored is reset to default when set to 0.
     c:             Cycle time of CPMG sequence
     norm_noise:    normalize intensity for a constant noise level whatever lb or n
                    is used
     e:             only add even echoes
     o:             only add odd echoes
    """

    import sys
    import os
    import os.path
    import subprocess
    # if this function is called from imported module then one needs to import TOPSPIN functions
    # so that they are available in the current namespace
    from TopCmds import CURDATA, GETPAR, GETPARSTAT, PUTPAR, RE, INPUT_DIALOG, MSG

    # installation directory is relative to current script location
    DIRINST = os.path.dirname(sys.argv[0])+"/../"
    print(DIRINST)
    # where is the external python executable
    CPYTHON = os.getenv('CPYTHON', "NotDefined")
    if "python" not in CPYTHON:
            MSG("CPYTHON environment not defined")
            EXIT()

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

    D3 = float(GETPARSTAT("D 3"))*1e6
    D6 = float(GETPARSTAT("D 6"))*1e6
    if args.c:
        cycle = args.c
    else:
        cycle = float(GETPARSTAT("P 60"))
        if cycle < 1:  
            # P60 is not likely to have stored the cycle time then uses historic calculation
            P4 = float(GETPARSTAT("P 4"))
            cycle = 2*(D3+D6) + P4
        cycle = str(cycle)

    if args.echo_position:
        echo_position = args.echo_position
    else:
        echo_position = GETPAR("USERP2")
        try : 
            echo_position = int(echo_position)
            if echo_position > 0:
                echo_position = str(echo_position)
            else:
                echo_position = str(D3+D6)
        except ValueError: 
            echo_position = str(D3+D6)

    if args.n: 
        N = args.n 
    else:
        N = GETPAR("USERP3")
        try : 
            N = int(N)
            if N > 0:
                N = str(N)
            else : 
                N = str(1+int(GETPARSTAT("L 22")))
        except ValueError: 
            N = str(1+int(GETPARSTAT("L 22")))
            
    if not args.noDialog:
        result = INPUT_DIALOG("processing parameters", 
          """Please provide:
          the gaussian broadening (GB) applyied to each echo, 
          the exponential decay that weight the different echoes, 
          the number N of echoes to sum,
          the position of first echo with respect to start of FID (not including 
             digital filter). Echo position defaults to D3+D6, 
             setting it to 0 resets it to default.
          the cycle time of the sequence
          """, 
             ["GB = ", "LB=", "N", "cycle time (us)", "echo position µs"], 
             [GB, LB, N, cycle, echo_position])
        try :
            (GB, LB, N, cycle, echo_position) = result
        except TypeError: 
            EXIT()

    PUTPAR("LB", LB)
    PUTPAR("USERP1", GB)
    PUTPAR("USERP2", echo_position)
    PUTPAR("USERP3", N)

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
        opt_args += "--norm_noise "
    if  args.e:
        opt_args += "-e "
    if  args.o:
        opt_args += "-o "
        


    script = os.path.expanduser(DIRINST+"/CpyBin/qcpmgadd_.py")
    # os.system(" ".join((CPYTHON, script, opt_args, fulldataPATH)))
    print([CPYTHON]+[script]+opt_args.split()+[fulldataPATH])    
    subprocess.call([CPYTHON]+[script]+opt_args.split()+[fulldataPATH])    

    RE(dataset)

if __name__ == '__main__':
    try : 
        import argparse
        parser  =  argparse.ArgumentParser(
            description='Add echoes in a qcpmg bruker experiment')
        parser.add_argument('-l', '--lb', type = str, 
            help='Lorentzian broadening applied to the decaying echo', default=0)
        parser.add_argument('-g', '--gb', type = str, 
            help='Gaussian broadening applied to each echo', default=0)
        parser.add_argument('-n', type = str, 
            help='Number of echo to sum', default=0)
        parser.add_argument('-c', type = str, help='qcpmg cycle in us', default=0)
        parser.add_argument('--echo_position', type=float, 
            help='echo position from start of FID (digital filter excluded) in us')
        parser.add_argument('--noDialog',action='store_true', 
            help='Do not show dialog : use default or provided optional arguments')
        parser.add_argument('--norm_noise',action='store_true', 
            help='Normalize noise as function of number of echoes added.')
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-e', action='store_true', help='Sum only even echoes')
        group.add_argument('-o', action='store_true', help='Sum only odd echoes')
        
        args  =  parser.parse_args(sys.argv[1:])
    except ImportError as ex:
        if len(sys.argv) > 1:
            MSG("Argparse module not found!\n Arguments won't be processed")
        class dummy():
            def __init__(self):
                self.lb = 0
                self.gb = 0
                self.n = 0
                self.c = 0
                self.echo_position = 0
                self.noDialog = False
                self.norm_noise = False
                self.e = False
                self.o = False
        args = dummy()
    except SystemExit as sysexit:
        MSG("Argument error : check console for help.")
        EXIT()
    dataset = CURDATA()
    add_echoes(args)
