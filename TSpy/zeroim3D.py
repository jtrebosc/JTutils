# -*- coding: utf-8 -*-
import sys

import os
PYTHONPATH=os.getenv("PYTHONPATH","not_defined")
if "not_defined" in PYTHONPATH:
	MSG("cannot acces to PYTHONPATH environment. It's required for accessing to brukerPARIO lib" )
	EXIT()
#add the Library path for importing brukerPARIO
sys.path.append(PYTHONPATH)

import brukerPARIO

from os.path import getsize 
# from os import system as execute
import subprocess

def get_os_version():
    ver = sys.platform.lower()
    if ver.startswith('java'):
        import java.lang
        ver = java.lang.System.getProperty("os.name").lower()
    return ver

OS=get_os_version()

dt=CURDATA()
dat=brukerPARIO.dataset(dt)
fn3iii=dat.returnprocpath()+"/3iii"

try :
    sz3iii=getsize(fn3iii)
except : 
    MSG("No file 3iii")
    EXIT()

if OS.startswith('mac') or OS.startswith('linux'):
    # for Linux with wine
    CMD="dd if=/dev/zero of=%s bs=%d count=1" % (fn3iii,sz3iii)
else:
    # for windows using topspin cygwin setup
    CMD="to be defined"
    MSG("not implemented for Windows yet")
    EXIT()
# execute(CMD)
subprocess.call(CMD.split())

