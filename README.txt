JTutils is a set of python scripts that enhance processing capabilites of 
Topspin

WARNING : use of these script WILL CORRUPT your Bruker data (in sense of GPL: good Laboratory Practice):
    no MD5 signature of files is done
    no auditing is done
The script will modify in place fid, ser, acqu(123)(s), 1r, 2rr etc... files


JTutils sets of script comprises:
	JTutils/TSpy : contains the python scripts run under Topspin environment
	JTutils/CpyBin : contains C python scritps usually called from TSpy
                     scripts (but then can be run as standalone scripts)
	JTutils/CpyLib : contains python library to read/write Bruker data

Developped with python 2.7 (ubuntu, macosx/topspin 4)
Tested (a bit) with python 2.4 (centos 5/topspin 2.1)

Requirements for running python program: 
 - in CpyLib: bruker.py or brukerPAR.py package will needs at least
	* python 2.2 
	* numpy 1.7
- in CpyBin : same requirement as CpyLib + processing module for covariance script
- in TSpy : all scripts should work with topspin provided jython version except for argparse which comes only in jython 2.7 
which in part of topspin >=3.5.
Scripts can run without but adding argparse is easy :
copy argparse.py file found at https://github.com/ThomasWaldmann/argparse/ in <TOPSPIN_DIR>/jython/Lib/ directory

other used standard modules :
sys
os
math
shutil
re
array

INSTALLATION
1) Copy all folder JTutils to destination directory DESTDIR

2) In Topspin preferences, set [DESTDIR]/JTutils/TSpy as scanned directory
   for python script

3) Install a working python + numpy environment (tested with anaconda on 
   MacOSX and windows)

4) Update the environment variables to define:
     CPYTHON = <path to the C python executable file> (required to run the JTutils/CpyBin scripts)
     PYTHONPATH = <Path to JTutils/CpyLib> (required to locate the bruker library from TSpy and CpyBin scripts.)

Details about step 4)

On Linux : 
If you launch from a terminal
add the lines to your ~/.bash_profile (if running bash)
DIRINSTALL=your_path_to_JTutils
if [ -z "$PYTHONPATH" ] ; then
    export PYTHONPATH=$DIRINSTALL/JTutils/CpyLib
elif [ -z $(echo $PYTHONPATH | grep "$DIRINSTALL/JTutils/CpyLib") ] ; then
    export PYTHONPATH=${PYTHONPATH}:$DIRINSTALL/JTutils/CpyLib
fi
export CPYTHON="PATH_TO_PYTHON_EXE"    # (e.g. /usr/bin/python)

Under Ubuntu, for example, the .bashrc/.bash_profile variables are not exposed to applications launched through graphical menus
You need to add the variable definitions (PYTHONPATH="your path", CPYTHON= "PATH_TO_PYTHON_EXE") to a file called .pam_environment in your home directory

On MacOSX:
Add the following two lines to your ~/.bash_profile
export PYTHONPATH=[DESTDIR]/JTutils/CpyLib/
export CPYTHON=[PATH_TO_PYTHON_EXE] (e.g. /usr/bin/python)

Follow instructions from https://github.com/ersiner/osx-env-sync to synchronize 
the environment variables from .bash_profile with launchd to ensure that 
environment variables are available in topspin GUI instance.

on Windows :
setup your environment variables according to instructions at
https://msdn.microsoft.com/en-us/library/windows/desktop/ms682653(v=vs.85).aspx

On windows 10 + anaconda python 2.7, it has been observed a probem with DLL 
not found when importing numpy in scripts launched from topspin 4.
Topspin 4 for windows redefines the PATH variable. 
The consequence is external programs like anaconda python that seems to
rely on PATH to find dll (notably for numpy) will fail.
For now the workaround is to edit topspin.cmd file to modify the line 
that redefines the PATH variable to add ";%Path%" at the end of it.

Old versions of topspin :
Old versions of topspin are using too old version of jython. This version can be updated by changing jython.jar file found in TOPSPIN_INSTALL_DIR/classes/lib/ with one more recent. Be aware that jython.jar files on jython website also depend on java version. For example, only jython version up to 2.5 can be installed on topspin 2.1 since higher versions of jython (2.7) require java 7 while topspin 2.1 only provides java 6.
For jython versions <2.7, argparse module can be installed in TOPSPIN_INSTALL_DIR/jython/Lib
