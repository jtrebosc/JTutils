# -*- coding: utf-8 -*-
help=""" 
Lists given parameter for all expno in current expname
syntax:  listAcquPar param [1|2] [s]
param : parameter as read (case sensitive!) in acqu(s). 
				If parameter is an array value, the index must be 
				provided after a dot.
				example : D.1  PLW.21 
options:
	1|2 : 1 read in dimension 1 (acqu(s))
				2 read in dimension 2 (acqu2(s))
	s   : read status parameter (acqus or acqu2s)
"""

import os
import sys

from JTutils import brukerPAR

try: 
    args = sys.argv[1:]
    test = args[0]
except : 
    MSG(help)
    EXIT()

param = args[0]
param = param.replace('.', ' ')
if '2' in args[1:] : 
    D = 2
else :
    D = 1

if 's' in args[1:] : 
    S = True
else : 
    S = False

MSG("looking in dimension %d and file status %s" % (D,S))
def searchAcqus(initdir):
    """ search the acqus file in sub-directory of initdir"""
    import os, fnmatch
    pattern = 'acqus'
    liste = []
    for path, dirs, files in os.walk(os.path.abspath(initdir)):
        for filename in fnmatch.filter(files, pattern):
            liste.append(path)
    return liste

dataset = CURDATA()

dt = brukerPAR.dataset(dataset)

expnamedir = dt.returnacqpath() + '/../'

expnoList = searchAcqus(expnamedir)
res = []
for i in expnoList :
    dataset = brukerPAR.splitprocpath(i + '/pdata/1/')
    dt = brukerPAR.dataset(dataset)
    expno = dt.dataset[1]
    val = dt.readacqpar(param, status=S, dimension=D)
    res.append("%s\t%s" % (str(expno), str(val)))
res.sort(key=lambda s : int(s.split()[0]))
print "looking for '" + " ".join(args) + "' in " + expnamedir
print('\n'.join(res))
MSG('\n'.join(res))
