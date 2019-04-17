# -*- coding: utf-8 -*-
## does summation of echoes using external python script
## new writing in a module like fashion in order to be able to call it from another python script
def add_echoes(lb=None, gb=None, n_echoes=None, cycle=None, echo_position=None, norm_noise=False, 
                odd_only=False, even_only=False, noDialog=False, dataset=None):
    """
    This function applies a gaussian apodization to each echo of a cpmg acquisition
    that used qcpmg.jt pulse sequence by calling an external python program.
    All echoes are added together with a weight using exponential multiplication 
    corrresponding to a spiklet broadening LB (Hz)
    It may be used for other pulse sequences.
     gb:            gaussian broadening (Hz) (default uses value stored in USERP1)
     lb:            lorentzian broadening for echo weighting (default uses value stored in LB)
     n:             number of echoes to add (if -1 uses value stored in USERP3)
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
    import JTutils
    try :
        CPYTHON = JTutils.get_cpython_path()
    except ValueError:
        _, msg, _ = sys.exc_info()
        MSG(str(msg))
        EXIT()
    SCRIPT = JTutils.CpyBin_path_to('qcpmgadd_.py')

# whether CURDATA should be called here or specific dataset should be provided as argument is not clear
    if dataset == None:
        dataset = CURDATA()
        RE(dataset)
    # process the arguments that are handled by this script
    if lb == None:
        lb = GETPAR("LB")

    if gb == None:
        gb = GETPAR("USERP1")
        try : 
            test_gb = float(gb)
        except ValueError:
            noDialog = True

    D3 = float(GETPARSTAT("D 3"))*1e6
    D6 = float(GETPARSTAT("D 6"))*1e6
    if cycle == None:
        cycle = float(GETPARSTAT("P 60"))
        if cycle < 1:  
            # P60 is not likely to have stored the cycle time then uses historic calculation
            P4 = float(GETPARSTAT("P 4"))
            cycle = 2*(D3+D6) + P4
        cycle = str(cycle)

    if echo_position == None:
        echo_position = GETPAR("USERP2")
        try : 
            echo_position = int(echo_position)
            if echo_position > 0:
                echo_position = str(echo_position)
            else:
                echo_position = str(D3+D6)
        except ValueError: 
            echo_position = str(D3+D6)

    if n_echoes == None: 
        n_echoes = GETPAR("USERP3")
        try : 
            n_echoes = int(n_echoes)
            if n_echoes > 0:
                n_echoes = str(n_echoes)
            else : 
                n_echoes = str(1+int(GETPARSTAT("L 22")))
        except ValueError: 
            n_echoes = str(1+int(GETPARSTAT("L 22")))
            
    if not noDialog:
        result = INPUT_DIALOG("processing parameters", 
          """Please provide:
          the gaussian broadening (GB) applyied to each echo, 
          the exponential decay that weight the different echoes in terms of line broadening (LB), 
          the number N of echoes to sum,
          the cycle time of the sequence
          the position of first echo with respect to start of FID (not including 
             digital filter). Echo position defaults to D3+D6, 
             setting it to 0 resets it to default.
          """, 
             ["GB = ", "LB=", "N", "cycle time (us)", "echo position (us)"], 
             [gb, lb, n_echoes, cycle, echo_position])
        try :
            (gb, lb, n_echoes, cycle, echo_position) = result
        except TypeError: 
            EXIT()

    PUTPAR("LB", lb)
    PUTPAR("USERP1", gb)
    PUTPAR("USERP2", echo_position)
    PUTPAR("USERP3", n_echoes)

    fulldataPATH = JTutils.fullpath(dataset)

    opt_args = " -g %s -l %s -n %s -c %s " % (gb, lb, n_echoes, cycle)
    if norm_noise:
        opt_args += "--norm_noise "
    if  even_only:
        opt_args += "-e "
    if  odd_only:
        opt_args += "-o "

    print([CPYTHON]+[SCRIPT]+opt_args.split()+[fulldataPATH])    
    subprocess.call([CPYTHON]+[SCRIPT]+opt_args.split()+[fulldataPATH])    


if __name__ == '__main__':
    try : 
        import argparse
        parser  =  argparse.ArgumentParser(
            description='Add echoes in a qcpmg bruker experiment')
        parser.add_argument('-l', '--lb',  
            help='Lorentzian broadening applied to the decaying echo', default=None)
        parser.add_argument('-g', '--gb',  
            help='Gaussian broadening applied to each echo', default=None)
        parser.add_argument('-n', 
            help='Number of echo to sum', default=None)
        parser.add_argument('-c', help='qcpmg cycle in us', default=None)
        parser.add_argument('--echo_position', default=None,
            help='echo position from start of FID (digital filter excluded) in us')
        parser.add_argument('--noDialog',action='store_true', 
            help='Do not show dialog : use default or provided optional arguments')
        parser.add_argument('--norm_noise',action='store_true', 
            help='Normalize noise as function of number of echoes added.')
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-e', action='store_true', help='Sum only even echoes')
        group.add_argument('-o', action='store_true', help='Sum only odd echoes')
        
        args  =  parser.parse_args(sys.argv[1:])
    except ImportError:
        if len(sys.argv) > 1:
            MSG("Argparse module not found!\n Arguments won't be processed")
        class dummy():
            def __init__(self):
                self.lb = None
                self.gb = None
                self.n = None
                self.c = None
                self.echo_position = None
                self.noDialog = False
                self.norm_noise = False
                self.e = False
                self.o = False
        args = dummy()
    except SystemExit:
        MSG(""" Script is exiting : either you asked for help or there is an argument error.
        Check console for additional information
        """  + parser.format_help() )
        EXIT()
    dataset = CURDATA()
    add_echoes(lb=args.lb, gb=args.gb, n_echoes=args.n, cycle=args.c, echo_position=args.echo_position,
                norm_noise=args.norm_noise, odd_only=args.e, even_only=args.o, noDialog=args.noDialog,
                dataset=dataset)
    RE(dataset)
