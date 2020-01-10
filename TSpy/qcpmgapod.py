# -*- coding: utf-8 -*-
## perform apodization of echoes using external python script
## new writing in a module like fashion in order to be able to call it from another python script
def apodize_echoes(gb=None, cycle=None, echo_position=None, noDialog=False, dataset=None):
    """
    This function applies a gaussian apodization to each echo of a cpmg acquisition
    that used qcpmg.jt pulse sequence by calling an external python program.
    It may be used for other pulse sequences.
    If a variable is set to None a default value is chosen
     gb:            gaussian broadening (Hz) (default value stored in USERP1)
     echo_position: Position of echo with respect to start of FID (not including digital filter)
          Position is read/stored in USERP1 if None, it defaults to D3+D6. The value stored is 
          reset to default if set to 0.
     cycle:             Cycle time of CPMG sequence
    """

    import sys
    import os
    import os.path
    import subprocess
    # if this function is called from imported module then one needs to import TOPSPIN functions
    # so that they are available in the current namespace
    from TopCmds import CURDATA, GETPAR, GETPARSTAT, PUTPAR, RE, INPUT_DIALOG, MSG
    import JTutils

# whether CURDATA should be called here or specific dataset should be provided as argument is not clear
    if dataset == None:
        dataset = CURDATA()
        RE(dataset)
    # process the arguments that are handled by this script

    if gb == None: 
        gb = GETPAR("USERP1")
        try : 
            test_gb = float(gb)
        except ValueError:
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
            echo_position = int(echo_position)
            if echo_position > 0:
                echo_position = str(echo_position)
            else:
                echo_position = str(D3+D6)
        except ValueError: 
            echo_position = str(D3+D6)

    if not noDialog:
        result = INPUT_DIALOG("processing parameters", 
          """Please provide 
          the gaussian broadening (GB) applyied to each echo,
          the cycle time of the sequence 
          the position of first echo with respect to start of FID 
            (not including digital filter) Echo position defaults to D3+D6, 
            setting it to 0 resets it to default.
          """, 
             ["GB (Hz)=", "cycle time (us)", "echo position (default=D3+D6) (us)"],
             [gb, cycle, echo_position])
        try :
            (gb, cycle, echo_position) = result
        except TypeError: 
            EXIT()
    PUTPAR("USERP1", gb)
    PUTPAR("USERP2", echo_position)

    fulldataPATH = JTutils.fullpath(dataset)

    opt_args = " -g %s -c %s -s %s" % (gb, cycle, echo_position)

    script = JTutils.CpyBin_script("qcpmgapod_.py")
    # os.system(" ".join((JTutils.CPYTHON, script, opt_args, fulldataPATH)))
    subprocess.call([JTutils.CPYTHON] + [script] + opt_args.split() + [fulldataPATH])    
    RE(dataset)

if __name__ == '__main__':
    class dummy():
        def __init__(self):
            self.gb = None
            self.c = None
            self.echo_position = None
            self.noDialog = False
    try : 
        import argparse
        parser  =  argparse.ArgumentParser(description='Add echoes in a qcpmg bruker experiment')
        parser.add_argument('-g', '--gb', help='Gaussian broadening applied to each echo', default=None)
        parser.add_argument('-c', help='qcpmg cycle in us', default=None)
        parser.add_argument('--echo_position', default=None,
           help='echo position from start of FID (digital filter excluded) in us')
        parser.add_argument('--noDialog', action='store_true', help='Do not show dialog : use default or provided optional arguments')
        
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
    apodize_echoes(gb=args.gb, cycle=args.c, echo_position=args.echo_position, noDialog=args.noDialog, dataset=dataset)
