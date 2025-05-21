# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import JTutils

def read_mdisp(dataset):
    """ Read the assocs file in dataset procno and search for files defined for multiple display """
    dtst = JTutils.brukerPARIO.dataset(dataset)
    procpath = dtst.returnprocpath()
    fname = procpath + 'assocs'
    if os.path.isfile(fname):
        mdisp = dtst._readpar(procpath + 'assocs', "MULTDISP")
        return mdisp.split('|')
    return []

def getfilename(procnopath, isfid):
    """ returns the filename to read given the fullpath to procno and whether fid or spectrum is to be loaded"""
    from JTutils import brukerPARIO as io
    the_path = io.splitprocpath(procnopath)
    dataset = io.dataset(the_path)
    if isfid:
        dim = dataset.readacqpar('PARMODE', True, 1)
        if dim == 0:
            file = 'fid'
        else :
            file = 'ser'
        return os.path.join(dataset.returnacqpath(), file)
    else:
        return os.path.join(dataset.returnprocpath(), '')
    

def launch_ssnake(datfiles, config):
    """ datfiles : list of fully qualified files to open
        config:  configuration dictionnary defining where to find exe files
    """
    try:
        ssnake_path = config['SSNAKEPATH']
    except KeyError:
        MSG("Sorry config file doesn't contain proper SSNAKEPATH")
        EXIT()
    args = []
    
    for f in datfiles:
        args.append(f) 
        
    JTutils.run_ext_script(ssnake_path, args)

if __name__ == '__main__':
    from JTutils.TSpy.ssnake_setup import read_config_file, run_setup
    from JTutils import fullpath, _run_string_ext_script

    try:
        version_script = """import sys
print(sys.version)"""
        version = _run_string_ext_script(version_script)
        if not version.startswith('3'): 
            MSG("""Warning external python defined in JTutils setup not version 3!
                   SSNAKE execution may fail...""")
    except Exception as e:
        MSG(str(e))
        MSG("Failed to test python version: check JTutils installation (run 'setup_JTutils -r')")
    try :
        config = read_config_file()
    except Exception as e:
        MSG(str(e))
        MSG("Failed to read configuration file. Let's launch the setup procedure...")
        run_setup()
        EXIT()
    if config == dict():
        MSG("Configuration is empty. Let's launch the setup procedure...")
        run_setup()
        EXIT()
    # argparse prints help messages to stdout and error to stderr so we need to redirect these to get argument errors or help
    from StringIO import StringIO
    import sys
    old_stdout = sys.stdout
    old_stderr = sys.stderr

    my_stdout = StringIO()
    sys.stdout = my_stdout
    sys.stderr = my_stdout
    try : 
        import argparse
        HelpText = """Launch ssnake to open current dataset
    Several versions can be defined in configuration (see ssnake_setup.py)
"""
        parser  =  argparse.ArgumentParser(
            description='Launch ssnake to open current dataset')
        parser.add_argument('version', nargs='?',
            help='''Version of ssnake installed with ssnake_setup : 
currently installed versions are: %s''' % (', '.join(config.keys())), 
            default=None)
        parser.add_argument('-m', '--mdisp', help='Open all spectra from multiple display', action='store_true')     
        parser.add_argument('-f', '--fid', help='Reads time domain FID instead of spectrum', action='store_true')     
        args = parser.parse_args(sys.argv[1:])
        version = args.version
        mdisp = args.mdisp
        isfid = args.fid
    except ImportError:
        if len(sys.argv) > 1:
            version = sys.argv[1]
            mdisp = False
            isfid = False
        else: 
            version = None
            mdisp = False
            isfid = False
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
    
#    print config
    if version == None :
        for key in config.keys():
            if config[key]['DEFAULT']:
                version = key
                break
    try :
        setup_dict = config[version]
    except KeyError:
        MSG("""The version %s was not found in configuration file.
Allowed versions are : %s """  % (version, ', '.join(config.keys())))
        EXIT()

    current_data = CURDATA()
    if JTutils._OS == 'win':
        current_data[0].replace('/', '\\')
    if current_data is None:
        datfiles = []
    else:
        datfiles = [getfilename(fullpath(current_data), isfid)]
        if mdisp :
            mfiles = read_mdisp(current_data)
            for f in mfiles:
                datfiles.append(getfilename(f, isfid))
    launch_ssnake(datfiles, setup_dict)
 
