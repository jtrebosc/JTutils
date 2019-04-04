# -*- coding: utf-8 -*-
## perform apodization of echoes using external python script
## new writing in a module like fashion in order to be able to call it from another python script
def apodize_echoes(args):
    """
    This function applies a gaussian apodization to each echo of a cpmg acquisition
    that used qcpmg.jt pulse sequence by calling an external python program.
    It may be used for other pulse sequences.
    It takes one parameter args that is a class with the mandatory following 
    variables:
        args.gb
        args.c
        args.echo_position
    If a variable is set to None a default value is chosen
     gb:            gaussian broadening (Hz) (default value stored in USERP1)
     echo_position: Position of echo with respect to start of FID (not including digital filter)
          Position is stored in USERP1, it defaults to D3+D6. The value stored is 
          reset to default if set to 0.
     c:             Cycle time of CPMG sequence
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
    # where is the external python executable
    CPYTHON = os.getenv('CPYTHON', "NotDefined")
    if "python" not in CPYTHON:
            MSG("CPYTHON environment not defined")
            EXIT()
    # MSG(CPYTHON)

# whether CURDATA should be called here or specific dataset should be provided as argument is not clear
    dataset = CURDATA()
    RE(dataset)
    # process the arguments that are handled by this script

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

    if not args.noDialog:
        result = INPUT_DIALOG("processing parameters", 
          """Please provide the gaussian broadening (GB) applyied to each echo,
          cycle time of the sequence and position of first echo with respect to
          start of FID (not including digital filter)
          Echo position defaults to D3+D6, setting it to 0 resets it to default.
          the cycle time of the sequence
          """, 
             ["GB (Hz)=", "cycle time (us)", "echo position (default=D3+D6) (us)"],
             [GB, cycle, echo_position])
        try :
            (GB, cycle, echo_position) = result
        except TypeError: 
            EXIT()
    PUTPAR("USERP1", GB)
    PUTPAR("USERP2", echo_position)

    # special treatment for topspin<3
    def fullpath(dataset):
        dat=dataset[:] # make a copy because I don't want to modify the original array
        if len(dat) == 5: # for topspin 2-
                dat[3] = "%s/data/%s/nmr" % (dat[3], dat[4])
        fulldata = "%s/%s/%s/pdata/%s/" % (dat[3], dat[0], dat[1], dat[2])
        return fulldata
    fulldataPATH=fullpath(dataset)

    opt_args = " -g %s -c %s -s %s" % (GB, cycle, echo_position)

    script = os.path.expanduser(DIRINST+"/CpyBin/qcpmgapod_.py")
    # os.system(" ".join((CPYTHON, script, opt_args, fulldataPATH)))
    subprocess.call([CPYTHON] + [script] + opt_args.split() + [fulldataPATH])    
    RE(dataset)

if __name__ == '__main__':
    try : 
        import argparse
        parser  =  argparse.ArgumentParser(description='Add echoes in a qcpmg bruker experiment')
        parser.add_argument('-g', '--gb', type = str, help='Gaussian broadening applied to each echo', default=0)
        parser.add_argument('-c', type = str, help='qcpmg cycle in us', default=0)
        parser.add_argument('--echo_position', type=float, 
           help='echo position from start of FID (digital filter excluded) in us')
        parser.add_argument('--noDialog',action='store_true', help='Do not show dialog : use default or provided optional arguments')
        
        args  =  parser.parse_args(sys.argv[1:])
    except ImportError as ex:
        if len(sys.argv) > 1:
            MSG("Argparse module not found!\n Arguments won't be processed")
        class dummy():
            def __init__(self):
                self.gb = 0
                self.c = 0
                self.echo_position = 0
                self.noDialog = False
        args = dummy()
    except SystemExit as sysexit:
        MSG("Argument error : check console for help.")
        EXIT()
    dataset = CURDATA()
    apodize_echoes(args)
