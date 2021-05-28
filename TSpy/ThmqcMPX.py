# -*- coding: utf-8 -*-
## convert multiplexed(F1) hmqc 3D data into Echoe AntiEchoe 2D dataset

def mutiplex2EAE(Qlevel=None, MC2=None, noDialog=False, dataset=None):
    """The function converts a dataset stored as multiplex into an Echoe/Anti-echoe type acquisition.
       The dataset must be a 2D extracted F2F3 plane from 3D with F1 being the multiplexed dimension 
       (use "rpl 23 1 11" for example) 
       Qlevel is the quantum level to be selected from multiplex
       MC2 is how the data will be stored in topspin format (see MC2 processing parameter)
       default MC2 is read from F1 of the 2D plane
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
    if MC2 == None:
        MC2 = GETPAR("1 MC2") # read MC2 from F1 (indirect 2D from rpl of 3D)
#    MSG(str(type(MC2)))
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

    opt_args = " -Q %s -m %s" % (Qlevel, MC2 )

    JTutils.run_CpyBin_script("ThmqcMPX_.py",  opt_args.split() + [fulldataPATH])
    RE(dataset)

if __name__ == '__main__':
    class dummy():
        def __init__(self):
            self.Qlevel = None
            self.MC2 = None
            self.noDialog = False
    try : 
        import argparse
        parser  =  argparse.ArgumentParser(description='Convert multiplex 2D to Echoe/Antiechoe acquisition.')
        parser.add_argument('-Q', '--Qlevel', help='Quantum level to select', default=None)
        parser.add_argument('-m', '--MC2', help='MC2 value to store result: default MC2 parameter', default=None)
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
    mutiplex2EAE(Qlevel=args.Qlevel, MC2=args.MC2, noDialog=args.noDialog, dataset=dataset)
