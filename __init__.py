# -*- coding: utf-8 -*-
from .CpyLib import brukerPAR 
__all__ = ['TSpy', 'brukerPAR', 'fullpath', 'get_cpython_path', 'CpyBin_path_to', 'CPYTHON', 'CpyBin' ]

# special treatment for topspin<3
def fullpath(dataset):
    """
    return absolute path to dataset
    dataset is an array as returned by CURDATA()
    """
    import os
    dat = dataset[:] # make a copy because I don't want to modify the original array
    if len(dat) == 5: # for topspin 2-
            dat[3] = os.path.join(dat[3], 'data', dat[4], 'nmr')
    fulldata = os.path.join(dat[3], dat[0], dat[1], 'pdata', dat[2])
    return fulldata

def get_cpython_path():
    """
    Return absolute path to external C python interpreter 
    as read from CPYTHON environment variable
    """
    from  os import getenv
    CPYTHON = getenv('CPYTHON', "NotDefined")
    if CPYTHON == "NotDefined":
        raise ValueError("CPYTHON variable environment not found")
        pass
    return CPYTHON

def CpyBin_path_to(name):
    """
    return absolute path to "name" script found in current module JTutils/CpyBin 
    """
    from os.path import dirname, abspath
    return dirname(abspath(__file__)) + "/CpyBin/" + name

CPYTHON = get_cpython_path()
CpyBin = CpyBin_path_to('')
