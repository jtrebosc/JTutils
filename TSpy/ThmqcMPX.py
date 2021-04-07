# -*- coding: utf-8 -*-
## convert multiplexed(F1) hmqc 3D data into Echoe AntiEchoe 2D dataset

def mutiplex2EAE(Qlevel=None, noDialog=False, dataset=None):
    """The function converts a dataset stored as multiplex into an Echoe/Anti-echoe type acquisition.
       The dataset must be a F2F3 plane with F1 being the multiplexed acquisition
       Qlevel is the quantum level to be selected from multiplex
       Processing assumes that multiplex dimension is stored with phase 2*pi*i/Nphases
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

    if Qlevel == None: 
        Qlevel = GETPAR("USERP1")
        try : 
            test_Qlevel = int(Qlevel)
        except ValueError:
            noDialog = False

    if not noDialog:
        result = INPUT_DIALOG("processing parameters", 
          """Please provide: 
            quantum level to select
          """, 
             [ "quantum level to select"],
             [Qlevel])
        try :
            ( Qlevel,) = result
        except TypeError: 
            EXIT()
    PUTPAR("USERP1", str(Qlevel))

    fulldataPATH = JTutils.fullpath(dataset)

    opt_args = " -Q %s " % (Qlevel, )

    JTutils.run_CpyBin_script("ThmqcMPX_.py",  opt_args.split() + [fulldataPATH])
    RE(dataset)

if __name__ == '__main__':
    class dummy():
        def __init__(self):
            self.Qlevel = None
            self.noDialog = False
    try : 
        import argparse
        parser  =  argparse.ArgumentParser(description='Convert multiplex 2D to Echoe/Antiechoe acquisition.')
        parser.add_argument('-Q', '--Qlevel', help='Quantum level to select', default=None)
        parser.add_argument('--noDialog', action='store_true', help='Do not show dialog : use default, stored or provided optional arguments')
        
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
    mutiplex2EAE(Qlevel=args.Qlevel, noDialog=args.noDialog, dataset=dataset)
