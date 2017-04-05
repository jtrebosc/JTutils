# -*- coding: utf-8 -*-
## does summation of echoes using external python script
import sys
import os
import os.path
import subprocess

# installation directory is relative to current script location
DIRINST=os.path.dirname(sys.argv[0])+"/../"
CPYTHON=os.getenv('CPYTHON',"NotDefined")

dataset=CURDATA()
LB=GETPAR("1 LB")
GB=GETPAR("LB")
s=GETPAR("USERP1")
c=GETPAR("USERP2")

res=INPUT_DIALOG("processing parameters", 
  """
  please provide  :
     the gaussian broadening (GB) applyied
     the slope for the gaussian center shift (1 for SQSQ or 2 for DQSQ for example).
     the center of gaussian or lorentzian in time excluding digital filter delay
     """, 
     ["GB=","slope=","center (usec)="],[GB,s,c])
(GB,s,c)=(res[0],res[1],res[2])
PUTPAR("LB",GB)
PUTPAR("USERP1",s)
PUTPAR("USERP2",c)

# special treatment for topspin<3
def fullpath(dataset):
	dat=dataset[:] # make a copy because I don't want to modify the original array
	if len(dat)==5: # for topspin 2-
	        dat[3]="%s/data/%s/nmr" % (dat[3],dat[4])
	fulldata="%s/%s/%s/pdata/%s/" % (dat[3],dat[0],dat[1],dat[2])
	return fulldata
fulldataPATH=fullpath(dataset)
opt_args=" -g %s -l %s -s %s -c %s" % (GB,"0",s,c)

script=os.path.expanduser(DIRINST+"/CpyBin/apod2D_.py")
# os.system(" ".join((CPYTHON,script,opt_args,fulldataPATH)))
subprocess.call([CPYTHON]+[script]+opt_args.split()+[fulldataPATH])
RE(dataset)
