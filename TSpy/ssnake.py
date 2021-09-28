# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import JTutils

def launch_ssnake(datfile, config):
    environment_var = os.environ.copy()
    if 'SSNAKEPATH' in config.keys():
        ssnake_path = config['SSNAKEPATH']

    subp_args = [JTutils.cpython_path(), ssnake_path]
    if datfile is not None:
        subp_args.append(datfile)
    subprocess.call(subp_args, env=environment_var)

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
        version = parser.parse_args(sys.argv[1:]).version
    except ImportError:
        if len(sys.argv) > 1:
            version = sys.argv[1]
        else: 
            version = None
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
    
    print config
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
    if current_data is None:
        datfile = None
    else:
        dataset = fullpath(current_data)
        dim = GETPROCDIM()
        if dim ==  1 :
            spectname = "1r"
        elif dim == 2 :
            spectname = "2rr"
        else :
            MSG("ssnake can only open 1D or 2D datasets")
            EXIT()
        datfile = os.path.join(dataset, spectname)
    launch_ssnake(datfile, setup_dict)
 
