# -*- coding: utf-8 -*-
# get information on current setup
# print information in MSG box, in console and it should propose to save the report in a file

import sys
import os
from os.path import abspath, dirname

version = sys.version
var_env = os.environ
curdir = os.getcwd()

scriptFile = sys.argv[0]
scriptDir = dirname(sys.argv[0])
CpyLibDir = scriptDir + '/../CpyLib'
CpyBinDir = scriptDir + '/../CpyBin'
XWINNMRHOME = os.getenv('XWINNMRHOME', "not Defined")
USERHOME_DOT_TOPSPIN = os.getenv('USERHOME_DOT_TOPSPIN', "not defined")
CPYTHON = os.getenv('CPYTHON', "not defined")
PYTHONPATH = os.getenv('PYTHONPATH', "not defined")

if (abspath(CpyLibDir) != abspath(PYTHONPATH)):
    WarningLibDir = """Warning : JTutils folder structure and PYTHONPATH are not consistent. 
You should make sure that PYTHON points to %s""" % (abspath(CpyLibDir),)
else :  WarningLibDir =  ""

message = """Current python version is: %s
Current working directory is : %s
Current python script is : %s
CpyLib is : %s
CpyBin is : %s
XWINNMRHOME is : %s
CPYTHON is : %s
PYTHONPATH is : %s
""" % (version,  curdir, scriptFile, CpyLibDir, CpyBinDir, XWINNMRHOME, CPYTHON, PYTHONPATH)	

import_report = "\n"
try :
    import JTutils
    import_report += "JTutils module imported successfully\n"
except ImportError:
    import_report += "ERROR: JTutils module import FAILED\n"
try :
    from JTutils import brukerPAR
    import_report += "brukerPAR module imported successfully\n"
except ImportError:
    import_report += "ERROR: brukerPAR module import FAILED\n"
try :
    import argparse
    import_report += "argparse module imported successfully\n"
except ImportError:
    import_report += """ERROR: argparse module import FAILED: you should consider installing argparse.py 
 in %s
 or %s \n""" % (XWINNMRHOME + "/jython/Lib/", XWINNMRHOME + "/exp/stan/nmr/py/user/",)
    import_report += "argparse.py module file can be downloaded from https://pypi.org/project/argparse/ website\n"

# how to run tests for external python configuration ?
# need to test that python can run, can import argparse, numpy and processing and return respective versions
import subprocess 

WarningCpython = "Checking CPYTHON configuration\n"

if CPYTHON=="not defined" :
    WarningCpython += """ERROR: CPYTHON variable is not defined in environnement
     you need to define CPYTHON environment variable 
     to a working excutable of python with numpy module\n"""
    cpython_available = False
else:
    CMD = """import sys
print(sys.version) """
    try:
        cpython_version = subprocess.check_output([CPYTHON,"-c", CMD], stderr=subprocess.STDOUT)
        WarningCpython += "%s version is %s\n" % (CPYTHON, cpython_version,)
        cpython_available = True
    except :
        exc, exc_mesg = sys.exc_info()[0:2]
        WarningCpython += "ERROR: %s raised an error: %s\n%s" % (CPYTHON, exc, exc_mesg)
        cpython_available = False

if cpython_available:
    CMD = """import numpy
print(numpy.__version__) """
    try:
        cnumpy_version = subprocess.check_output([CPYTHON,"-c", CMD], stderr=subprocess.STDOUT)
        WarningCpython += "in %s numpy module version is %s\n" % (CPYTHON, cnumpy_version,)
    except subprocess.CalledProcessError, exc:
        WarningCpython += "ERROR: numpy module in %s raised an error: %s\n" % (CPYTHON, exc.output,)

    CMD = """import argparse
print(argparse.__version__) """
    try:
        cargparse_version = subprocess.check_output([CPYTHON,"-c", CMD], stderr=subprocess.STDOUT)
        WarningCpython += "in %s argparse module version is %s\n" % (CPYTHON, cargparse_version,)
    except subprocess.CalledProcessError, exc:
        WarningCpython += "argparse module in %s raised an error: %s\n" % (CPYTHON, exc.output,)

    CMD = """import multiprocessing
print(multiprocessing.__version__) """
    try:
        cprocessing_version = subprocess.check_output([CPYTHON,"-c", CMD], stderr=subprocess.STDOUT)
        WarningCpython += "In %s multiprocessing module version is %s\n" % (CPYTHON, cprocessing_version,)
    except subprocess.CalledProcessError, exc:
        WarningCpython += "multiprocessing module in %s raised an error: %s \n" % (CPYTHON, exc.output,)

    CMD = """import bruker
print(bruker.__version__) """
    try:
        cbruker_version = subprocess.check_output([CPYTHON,"-c", CMD], stderr=subprocess.STDOUT)
        WarningCpython += "In %s bruker module version is %s\n" % (CPYTHON, cbruker_version,)
    except subprocess.CalledProcessError, exc:
        WarningCpython += "bruker module in %s raised an error: %s\n" % (CPYTHON, exc.output,)

message += WarningLibDir
message += import_report
message += WarningCpython
MSG(message)

env_list = "\nList of defined environment variables\n"
env_list += "\n".join(["%s: %s" % (key,var_env[key]) for key in var_env.keys()])

print(env_list)

save_report = CONFIRM(title="Save report", message="Do you want to save the report in a file ?")
if save_report :
    # add a file dialog to choose the directory and filename where to store report
    f = open("report.txt",'w')
    f.write(message)
    f.write(env_list)
    f.close()
    MSG("""report written in %s.""" % (curdir+"/report.txt",))

