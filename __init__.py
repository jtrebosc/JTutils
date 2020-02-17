# -*- coding: utf-8 -*-
# JTutils module should expose: 
#    brukerPAR submodule
#    TSpy submodule
#    fullpath utility (return fulpath to a dataset as returned by CURDATA Bruker function
#    CpyBin_script (returns the fullpath to script in CpyBin subfolder
#    CPYTHON variable that contains the CPYTHON executable path

from .CpyLib import brukerPAR 
__all__ = ['TSpy', 'brukerPAR', 'fullpath', 'CPYTHON', 'PYTHONPATH', 'CpyBin_script']

from os.path import dirname, abspath, join
import os
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

def _get_cpython_path():
    """
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

CPYTHON = _get_cpython_path()
_python_path = join(dirname(abspath(__file__)), "CpyLib")
environment = os.environ.copy()
if 'PYTHONPATH' in env:
    environment['PYTHONPATH'] = _python_path + ':' + environment['PYTHONPATH'] 
else:
    environment['PYTHONPATH'] = _python_path 

def CpyBin_script(script):
    """ return full path to "script" in CpyBin """
    return join(dirname(abspath(__file__)), "CpyBin", script)

def run_CpyBin_script(script_name, args):
    """
    launch CpyBin/scriptname with args using external CPYTHON
    script_name: name of external python script in CpyBin
    args : a list of strings : list of arguments to pass to script
    """
    import subprocess
    # get environment variable
    script = CpyBin_script(script_name)
    subprocess.call([CPYTHON]+[script]+args, env=environment)    
    

