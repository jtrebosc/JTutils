# -*- coding: utf-8 -*-
help=""" 
Lists given parameter for all expno in current expname
syntax:  listAcquPar [-Dn] [-s] param1 param2 ...  
param : parameter as read (case sensitive!) in acqu(s). 
				If parameter is an array value, the index must be 
				provided after a dot.
				example : D.1  PLW.21 
options: Not relying on argparse library
	-Dn : read in dimension n with n=1 is direct dimension up to dimension n (=PARMODE +1)
				e.g. -D3 reads in third dimension that is F1 in 3D dataset and acqu3s file
	-s   : read status parameter (acqus or acqu2s)
"""

import os
import sys

from JTutils import brukerPARIO

try: 
    args = sys.argv[1:]
    test = args[0]
except : 
    MSG(help)
    EXIT()

status = False
dimension = 1
params = []
for val in args:
    if '-s' in val:
        status = True
#        args.delete(val)
    elif '-D' in val:
        dimension = int(val[-1])
#        args.delete(val)
    else:
        val = val.replace('.', ' ')
        params.append(val)

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

dt = brukerPARIO.dataset(dataset)

expnamedir = dt.returnacqpath() + '/../'

expnoList = searchAcqus(expnamedir)

res = []
for i in expnoList :
    dataset = brukerPARIO.splitprocpath(i + '/pdata/1/')
    dt = brukerPARIO.dataset(dataset)
    if dimension > int(dt.readacqpar('PARMODE', status=status)) + 1:
        continue
    expno = dt.dataset[1]
    line = [expno]
    for param in params:
        try:
            val = dt.readacqpar(param, status=status, dimension=dimension)
        except ValueError:
            line.append('N.A.')
            continue
        line.append(str(val))
    res.append("\t".join(line))
res.sort(key=lambda s : int(s.split()[0]))
#print "looking for '" + " ".join(args) + "' in " + expnamedir
#print('\n'.join(res))
statusStr = "status" if status else ""
header = "Looking for %s parameters in dimension %s in %s\n" % (statusStr , str(dimension), expnamedir)
col_title = ["\t".join(["expno"] + ["'"+param+"'" for param in params]) ]

#INPUT_DIALOG_SHOW(title='readAcquPar', header=header, items=[None, None], values=[col_title, '\n'.join(res)], types=['1', '2'], buttons=['OK'])

VIEWTEXT(title='readAcquPar', header=header, text='\n'.join(col_title + res), modal=1)
