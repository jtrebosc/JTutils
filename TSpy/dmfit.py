# -*- coding: utf-8 -*-
import os
import subprocess
import sys

# test if exists prop_dir/JTutils/dmfit
# read dmfit_location line
# assign the location to dmfit_path var
# if does not exists : launch setup dialog
# option to launch several versions
# use of wine prefix
# what structure for file dmfit ?
# FILEPATH=version:/path/to/exec;version:path/to/exec
# WINEPREFIX=
# WINEPATH=
# what else ?
# setup option if no working dmfit :
# is setup file present ?
# are intialised variables valid ?
# if not : 
# search for wine, search for dmfit
# ask for prefix...
# need add all kind of check 

def launch_dmfit(datfile, config):
    from JTutils.TSpy.dmfit_setup import get_os_version
    environment_var = os.environ.copy()
    if 'DMFITPATH' in config.keys():
        dmfit_path = config['DMFITPATH']
    if 'WINEPATH' in config.keys():
        wine_path = config['WINEPATH']
    if 'WINEPREFIX' in config.keys():
        environment_var['WINEPREFIX'] = config['WINEPREFIX']

    OS = get_os_version()
    if OS.startswith('linux') or OS.startswith('mac'):
        #check for wine is exec
        subp_args = [wine_path, dmfit_path]
    else:
        # check for dmfit is exec
        subp_args = [dmfit_path]
    if datfile is not None:
        subp_args.append(datfile)
    subprocess.call(subp_args, env=environment_var)

if __name__ == '__main__':
    from JTutils.TSpy.dmfit_setup import read_config_file, run_setup
    from JTutils import fullpath

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
        HelpText = """Launch dmfit to open current dataset
    Several versions can be defined in configuration (see dmfit_setup.py)
"""
        parser  =  argparse.ArgumentParser(
            description='Launch dmfit to open current dataset')
        parser.add_argument('version', nargs='?',
            help='''Version of dmfit installed with dmfit_setup : 
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
            MSG("dmfit can only open 1D or 2D datasets")
            EXIT()
        datfile = os.path.join(dataset, spectname)
    launch_dmfit(datfile, setup_dict)
 
