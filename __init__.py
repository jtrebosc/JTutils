# coding: utf8 
# JTutils module should expose: 
#    brukerPAR submodule
#    TSpy submodule
#    fullpath utility (return fulpath to a dataset as returned by CURDATA Bruker function
#    run_CpyBin_script : a function that runs an external script from CpyBin in 
#                        a CPYTHON environment with correct PYTHONPATH
from __future__ import unicode_literals

__all__ = ['TSpy', 'brukerPAR', 'fullpath', 'run_CpyBin_script']
from .CpyLib import brukerPAR 
from os.path import dirname, abspath, join, normpath
import os


def _get_os_version():
    """ returns the underlying OS as lowercase string: 
        string contains either windows, linux or mac """ 
    import sys
    version = sys.platform.lower()
    if version.startswith('java'):
        import java.lang
        version = java.lang.System.getProperty("os.name").lower()
    return version

_OS = _get_os_version()
# _OS in [ 'linux', 'win', 'mac os x']

# special treatment for topspin<3
def fullpath(dataset):
    """
    return absolute path to dataset
    dataset is an array as returned by CURDATA()
    """
    dat = dataset[:] # make a copy because I don't want to modify the original array
    if len(dat) == 5: # for topspin 2-
            dat[3] = join(normpath(dat[3]), 'data', dat[4], 'nmr')
    fulldata = join(normpath(dat[3]), dat[0], dat[1], 'pdata', dat[2])
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
    prop_dir = normpath(prop_dir)
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
    config_file = os.path.join(normpath(prop_dir),'JTutils','config.json')
    with open(config_file, 'w') as f:
        json.dump(config, f)

def _get_cpython_path():
    """
    Obsolete function: not used anymore
    Return absolute path to external C python interpreter 
    as read from CPYTHON environment variable
    """
    from  os import getenv
    CPYTHON = normpath(getenv('CPYTHON', "NotDefined"))
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

    if 'EXTRA_PATH' in config:
        _environment['PATH'] = os.pathsep.join(config['EXTRA_PATH'] + 
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

    try:
        result = subprocess.check_output([_config['CPYTHON'], "-c", script], 
                        env=_environment, stderr=subprocess.STDOUT)    
        if 'win' in _OS:
            # default codepage is cp850 on windows
            result = result.decode('cp850')
        return result
    except subprocess.CalledProcessError, exc:
    # We need to convert the output of exception 
    # to encoding to utf-8 then re raise the error
        if 'win' in _OS:
            error_message = exc.output.decode('cp850')
        else:
            error_message = exc.output
        raise subprocess.CalledProcessError(exc.returncode, exc.cmd, error_message)
 
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
    

