# -*- coding: utf-8 -*-
# JTutils module should expose: 
#    brukerPAR submodule
#    TSpy submodule
#    fullpath utility (return fulpath to a dataset as returned by CURDATA Bruker function
#    run_CpyBin_script : a function that runs an external script from CpyBin in 
#                        a CPYTHON environment with correct PYTHONPATH

__all__ = ['TSpy', 'brukerPAR', 'fullpath', 'run_CpyBin_script']
from .CpyLib import brukerPAR 
from os.path import dirname, abspath, join
import os

#_config = {'CPYTHON': "/usr/bin/python", 'PATH_EXTRA': []} 


# special treatment for topspin<3
def fullpath(dataset):
    """
    return absolute path to dataset
    dataset is an array as returned by CURDATA()
    """
    dat = dataset[:] # make a copy because I don't want to modify the original array
    if len(dat) == 5: # for topspin 2-
            dat[3] = join(dat[3], 'data', dat[4], 'nmr')
    fulldata = join(dat[3], dat[0], dat[1], 'pdata', dat[2])
    return fulldata


def _read_config():
    """ read json config file in user topspin preference folder 
        (.topspin1 for example)
        returns a dictionnary with configuration parameters
    """
    import json
    prop_dir = os.getenv('USERHOME_DOT_TOPSPIN', "not defined")
    if prop_dir == "not defined":
        print("USERHOME_DOT_TOPSPIN not defined")
        raise
    config_file = os.path.join(prop_dir,'JTutils','config.json')
    with open(config_file, 'r') as f:
        config = json.load(f)
    return config

def _write_config(config):
    """ write json config file in user topspin preference folder 
        (.topspin1 for example)
        argument config is a dictionnary with configuration parameters
    """
    import json
    prop_dir = os.getenv('USERHOME_DOT_TOPSPIN', "not defined")
    if prop_dir == "not defined":
        print("USERHOME_DOT_TOPSPIN not defined")
        raise
    config_file = os.path.join(prop_dir,'JTutils','config.json')
    with open(config_file, 'w') as f:
        json.dump(config, f)

def _get_cpython_path():
    """
    Obsolete function: not used anymore
    Return absolute path to external C python interpreter 
    as read from CPYTHON environment variable
    """
    from  os import getenv
    CPYTHON = getenv('CPYTHON', "NotDefined")
    if CPYTHON == "NotDefined":
        from TopCmds import MSG, EXIT
        msg  = """CPYTHON environment variable is not set: it must exist and 
point to an external C PYTHON interpreter !!! """
        MSG(msg)
        EXIT()
    return CPYTHON

def _set_external_environment(config):
    _python_path = join(dirname(abspath(__file__)), "CpyLib")
    # adjust
    _environment = os.environ.copy()
    if 'PYTHONPATH' in _environment:
        _environment['PYTHONPATH'] = os.pathsep.join([_python_path, _environment['PYTHONPATH']]) 
    else:
        _environment['PYTHONPATH'] = _python_path 

    if 'PATH_EXTRA' in config:
        _environment['PATH'] = os.pathsep.join(config['PATH_EXTRA'] + 
                                      [_environment['PATH']])
    return _environment

def _run_string_ext_script(script):
    """
    launch script using external CPYTHON
    script : string containing script to execute
    returns the output of script
    """
    import subprocess
    _config = _read_config()
    _environment = _set_external_environment(_config)
    return subprocess.check_output([_config['CPYTHON'], "-c", script], 
                        env=_environment, stderr=subprocess.STDOUT)    
    
def run_CpyBin_script(script_name, args):
    """
    launch CpyBin/script_name with args using external CPYTHON
    script_name: name of external python script in CpyBin
    args : a list of strings : list of arguments to pass to script
    """
    import subprocess
    _config = _read_config()
    _environment = _set_external_environment(_config)
    script = join(dirname(abspath(__file__)), "CpyBin", script_name)
    subprocess.call([_config['CPYTHON']]+[script]+args, env=_environment)    
    

