#encoding=utf-8
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
    import_report += "JTutils module import FAILED\n"
try :
    from JTutils import brukerPAR
    import_report += "brukerPAR module imported successfully\n"
except ImportError:
    import_report += "brukerPAR module import FAILED\n"
try :
    import argparse
    import_report += "argparse module imported successfully\n"
except ImportError:
    import_report += """argparse module import FAILED: you should consider installing argparse.py 
 in %s
 or %s \n""" % (XWINNMRHOME + "/jython/Lib/", XWINNMRHOME + "/exp/stan/nmr/py/user/",)
    import_report += "argparse.py module file can be downloaded from https://pypi.org/project/argparse/ website\n"

# how to run tests for external python configuration ?
# need to test that python can run, can import argparse, numpy and processing and return respective versions
import subprocess 

WarningCpython = "Checking CPYTHON configuration\n"

CMD = """import sys
print(sys.version) """
try:
    cpython_version = subprocess.check_output([CPYTHON,"-c", CMD], stderr=subprocess.STDOUT)
    WarningCpython += "CPYTHON version is %s\n" % (cpython_version,)
except :
    WarningCpython += "CPYTHON raised an error: %s" % (cpython_version,)

CMD = """import numpy
print(numpy.__version__) """
try:
    cnumpy_version = subprocess.check_output([CPYTHON,"-c", CMD], stderr=subprocess.STDOUT)
    WarningCpython += "CPYTHON numpy version is %s\n" % (cnumpy_version,)
except :
    WarningCpython += "numpy module in CPYTHON raised an error: %s\n" % (cnumpy_version,)

CMD = """import argparse
print(argparse.__version__) """
try:
    cargparse_version = subprocess.check_output([CPYTHON,"-c", CMD], stderr=subprocess.STDOUT)
    WarningCpython += "CPYTHON argparse version is %s\n" % (cargparse_version,)
except :
    WarningCpython += "argparse module in CPYTHON raised an error: %s\n" % (cargparse_version,)

CMD = """import processing
print(processing.__version__) """
try:
    cprocessing_version = subprocess.check_output([CPYTHON,"-c", CMD], stderr=subprocess.STDOUT)
    WarningCpython += "CPYTHON processing version is %s\n" % (cprocessing_version,)
except :
    WarningCpython += "processing module in CPYTHON raised an error: %s \n" % (subprocess.STDOUT,)

CMD = """import bruker
print(bruker.__version__) """
try:
    cbruker_version = subprocess.check_output([CPYTHON,"-c", CMD], stderr=subprocess.STDOUT)
    WarningCpython += "CPYTHON bruker version is %s\n" % (cbruker_version,)
except :
    WarningCpython += "bruker module in CPYTHON raised an error: %s\n" % (cbruker_version,)

message += WarningLibDir
message += import_report
message += WarningCpython
MSG(message)

env_list = "List of defined environment variables"
env_list += "\n".join(["%s: %s" % (key,var_env[key]) for key in var_env.keys()])

print(env_list)

