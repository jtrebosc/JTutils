# -*- coding: utf-8 -*-
""" 
A partir de l'expno courante liste un paramètre de processing 
 de toutes les expno présents dans le même expname 
 ne renvoi que les parametres dans le proc 1

appel avec  : listProcPar param [1|2] [s] 
   param doit être un paramètre tel que dans le fichier acqu
   1|2 dimension directe (1) ou indirecte (2) voir F3 (3)
   specifie s pour status parameter
les paramètres de type array (P, PLw...) doivent être appelés avec un point (.) 
séparateur entre le nom et l'index (P.index : P.17, P.24 etc...)
"""


import os

DIRINST = os.path.dirname(sys.argv[0])+"/../"
PYTHONPATH = os.getenv("PYTHONPATH")
#sys.path.append(PYTHONPATH)
if not PYTHONPATH in sys.path:
    sys.path.append(DIRINST+"CpyLib")
import brukerPARIO

args = sys.argv[1:]

param = args[0]
param = param.replace('.', ' ')
if '2' in args : D = 2
else : D = 1

if 's' in args : S = True
else : S = False

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

expnamedir = dt.returnacqpath()+'/../'

expnoList = searchAcqus(expnamedir)
res = []
for i in expnoList :
	dataset = brukerPARIO.splitprocpath(i+'/pdata/1/')
	dt = brukerPARIO.dataset(dataset)
	expno = dt.dataset[1]
	val = dt.readprocpar(param, status=S, dimension=D)
	res.append("%s\t%s" % (str(expno), str(val)))
res.sort(key=lambda s : int(s.split()[0]))
MSG('\n'.join(res))
print "looking for '"+" ".join(args)+"' in "+expnamedir
print '\n'.join(res)
