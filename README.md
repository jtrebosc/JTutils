# JTutils 
JTutils is a set of python scripts that enhance processing capabilites of 
Topspin.
JTutils script can load datasets from topspin in third party software like dmfit or ssNake.

Some scripts are specific to process data acquired with pulse sequences developped
in Lille, France by Julien TREBOSC. 

WARNING : use of these script WILL CORRUPT your Bruker data (in sense of GPL:
 Good Laboratory Practice):
* no MD5 signature of files is done
* no auditing is done

The script will modify in place fid, ser, acqu(123)(s), 1r, 2rr etc... files

The author decline any responsability for program or data loss that would result from the installation and use of these scripts.

JTutils sets of scripts comprise:
* JTutils/TSpy : contains the python scripts run under Topspin jython environment
* JTutils/CpyBin : contains C python scripts usually called from TSpy
  scripts (but then can be run as standalone scripts)
* JTutils/CpyLib : contains python library to read/write Bruker data

Developped mostly on python 3 (ubuntu, topspin 4, jython 2.7) so other platforms may have bugs.

## Requirements for running python program: 
Scripts are designed to run with the lowest version number possible. 
But with time tests were run with more recent versions. So minimum version 
can depend upon script.
 - in CpyLib: brukerIO.py or brukerPARIO.py package will needs at least
    * python 3.6
    * numpy 1.0.1 
 - in CpyBin : same requirement as CpyLib + processing module for covariance
  script
 - in TSpy : all scripts should work with topspin >=3.5 as provided jython is version 2.7

Running ssNake will require the associated modules (pyqt, scipy, numba, etc..).

Other used standard modules :
* sys
* os
* math
* shutil
* re
* array
* subprocess

## INSTALLATION
1) Install (unzip) folder JTutils to a destination directory DESTDIR.

2) Install a working python environment with all required modules (tested with 
   anaconda/miniconda on Linux, MacOSX and windows).

    For miniconda installation: 
        * Download miniconda (python3) at https://docs.conda.io/en/latest/miniconda.html
        * Run the miniconda installer (100-200Mb). All additional packages (numpy and others) can be automatically installed
           at step 4. 

3) In Topspin preferences, **Directories** section, "Manage source directories for edpul, edau etc. -> click *Change*
    * set [DESTDIR]/JTutils/TSpy as scanned directory for python scripts "JYTHON PROGRAMS" (**not python 3+ programs** )
    * then restart topspin for changes to take effect (not necessary for topspin > 4.5)

4) Run setup\_JTutils in topspin command bar:
    * It will ask for a python interpreter. It may have detetected several while searching for standard location of anaconda/miniconda.
    * if a conda (anaconda/miniconda) installation is selected it will check if it is in a conda environment 
    called JTutils. If not, it will ask if you want to create it. If yes it will automatically download all 
    modules required to run the JTutils scripts and ssNake.
    * It will test import of required modules. If the report does not point out any problem, everything should work!

