# -*- coding: utf-8 -*-
## does summation of echoes using external python script
## new writing in a module like fashion in order to be able to call it from another python script
def add_echoes(lb=None, gb=None, n_echoes=None, cycle=None, dead_pts=None, 
                echo_position=None, norm_noise=False, odd_only=False, 
                even_only=False, noDialog=False, skipFirst=False, dataset=None):
    """
    This function applies a gaussian apodization to each echo of a cpmg acquisition
    that used qcpmg.jt pulse sequence by calling an external python program.
    All echoes are added together with a weight using exponential multiplication 
    corrresponding to a spiklet broadening LB (Hz)
    It may be used for other pulse sequences.
     gb:            gaussian broadening (Hz) (default uses value stored in USERP1)
     lb:            lorentzian broadening for echo weighting (default uses value stored in LB)
     n_echoes:      number of echoes to add (if -1 or None uses value stored in USERP3)
                    invalid number or 0 defaults to L22+1
     cycle:             Cycle time of CPMG sequence
     dead_pts:      set dead_pts to zero at beginning and end of each echo.
     echo_position: Position of echo with respect to start of FID (not including digital filter)
          Position is stored in USERP1, it defaults to D3+D6. 
          The value stored is reset to default when set to 0.
     norm_noise:    normalize intensity for a constant noise level whatever lb or n
                    is used
     even_only:     only add even echoes
     odd_only:      only add odd echoes
     noDialog:      Don't show the interactive dialog
     skipFisrt:      Don't add the first echo (when affected by dead time)
    """

    import sys
    import os
    import os.path
    # if this function is called from imported module then one needs to import TOPSPIN functions
    # so that they are available in the current namespace
    from TopCmds import CURDATA, GETPAR, GETPARSTAT, PUTPAR, RE, INPUT_DIALOG, MSG
    import JTutils

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
            gb = "0"
            noDialog = False

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
            echo_position = float(echo_position)
            if echo_position > 0:
                echo_position = str(echo_position)
            else:
                echo_position = str(D3+D6)
        except ValueError: 
            echo_position = str(D3+D6)

    if dead_pts == None:
        dead_pts = GETPAR("TDoff") 
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
          - the gaussian broadening (GB) applyied to each echo, 
          - the exponential decay that weight the different echoes in terms of line broadening (LB), 
          - the number N of echoes to sum,
          - the cycle time of the sequence
          - dead time points to be removed at start and end of echoes
          - the position of first echo with respect to start of FID (not including 
             digital filter). Echo position defaults to D3+D6, 
             setting it to 0 resets it to default.
          """, 
             ["GB = ", "LB=", "N", "cycle time (us)", "dead points", "echo position (us)"], 
             [gb, lb, n_echoes, cycle, dead_pts, echo_position])
        try :
            (gb, lb, n_echoes, cycle, dead_pts, echo_position) = result
        except TypeError: 
            EXIT()

    PUTPAR("LB", lb)
    PUTPAR("USERP1", gb)
    PUTPAR("USERP2", echo_position)
    PUTPAR("USERP3", n_echoes)
    PUTPAR("TDoff", dead_pts)

    fulldataPATH = JTutils.fullpath(dataset)

    opt_args = " -g %s -l %s -n %s -c %s -s %s " % (gb, lb, n_echoes, cycle, echo_position)
    if norm_noise:
        opt_args += "--norm_noise "
    if  even_only:
        opt_args += "-e "
    if  odd_only:
        opt_args += "-o "
    if  skipFirst:
        opt_args += "-k "
    JTutils.run_CpyBin_script('qcpmgadd_.py', opt_args.split()+[fulldataPATH])


if __name__ == '__main__':
    # argparse prints help messages to stdout and error to stderr so we need to redirect these
    from StringIO import StringIO
    import sys
    old_stdout = sys.stdout
    old_stderr = sys.stderr

    my_stdout = StringIO()
    sys.stdout = my_stdout
    sys.stderr = my_stdout
    try : 
        import argparse
        parser  =  argparse.ArgumentParser(
            description='Add echoes in a qcpmg bruker experiment')
        parser.add_argument('-l', '--lb', default=None,
            help='Lorentzian broadening applied to the decaying echo')
        parser.add_argument('-g', '--gb',  
            help='Gaussian broadening applied to each echo', default=None)
        parser.add_argument('-n', 
            help='Number of echo to sum', default=None)
        parser.add_argument('-c', help='qcpmg cycle in us', default=None)
        parser.add_argument('-t', default=None, 
            help='dead time points to be removed at start and end of echo')
        parser.add_argument('--echo_position', default=None,
            help='echo position from start of FID (digital filter excluded) in us')
        parser.add_argument('--noDialog',action='store_true', 
            help='Do not show dialog : use default or provided optional arguments')
        parser.add_argument('--norm_noise',action='store_true', 
            help='Normalize noise as function of number of echoes added.')
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-e', action='store_true', 
            help='Sum only even echoes (count starting 0)')
        group.add_argument('-o', action='store_true', 
            help='Sum only odd echoes (count starting 0)')
        group.add_argument('-k', action='store_true', 
            help='Don\'t add (sKip) first echo')
        
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
                self.t = None
                self.echo_position = None
                self.noDialog = False
                self.norm_noise = False
                self.e = False
                self.o = False
                self.k = False
        args = dummy()
    except SystemExit:
        # argparse has triggered an exception : print the error in a MSG box
        # and restore the stdout and err
        err_msg = my_stdout.getvalue()
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        MSG(err_msg)
        print(err_msg)

        EXIT()

    err_msg = my_stdout.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    print(err_msg)

    dataset = CURDATA()
    add_echoes(lb=args.lb, gb=args.gb, n_echoes=args.n, cycle=args.c, 
                dead_pts=args.t, echo_position=args.echo_position,
                norm_noise=args.norm_noise, odd_only=args.e, even_only=args.o, 
                noDialog=args.noDialog, skipFirst=args.k, dataset=dataset)
    RE(dataset)
