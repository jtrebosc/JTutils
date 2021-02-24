JTutils is a set of python scripts that enhance processing capabilites of 
Topspin.

Some scripts are specific to process data acquired with pulse sequences developped
in Lille, France by Julien TREBOSC. 

WARNING : use of these script WILL CORRUPT your Bruker data (in sense of GPL:
 Good Laboratory Practice):
* no MD5 signature of files is done
* no auditing is done

The script will modify in place fid, ser, acqu(123)(s), 1r, 2rr etc... files

The author decline any responsability for program or data loss that would result from the installation and use of these scripts.

JTutils sets of scripts comprise:
* JTutils/TSpy : contains the python scripts run under Topspin environment
* JTutils/CpyBin : contains C python scritps usually called from TSpy
  scripts (but then can be run as standalone scripts)
* JTutils/CpyLib : contains python library to read/write Bruker data

Developped with python 2.7 (ubuntu, macosx/topspin 4).

Updated for python 3 (ubuntu, topspin 4).

## Requirements for running python program: 
Scripts are designed to run with the lowest version number possible. 
But with time tests were run with more recent versions. So minimum version 
can depend upon script
 - in CpyLib: brukerIO.py or brukerPARIO.py package will needs at least
    * python 2.5
    * numpy 1.0.1 
 - in CpyBin : same requirement as CpyLib + processing module for covariance
  script
 - in TSpy : all scripts should work with topspin provided jython version except
    for those using argparse and subprocess.check_call which exist only in 
    jython 2.7 which is provided within topspin >=3.5.


Other used standard modules :
* sys
* os
* math
* shutil
* re
* array
* subprocess

## INSTALLATION
1) Install folder JTutils to a destination directory DESTDIR.

2) Install a working python + numpy environment (tested with 
   anaconda/miniconda on Linux, MacOSX and windows).

   For miniconda installation: 
      1) download miniconda (python 2 or 3) at https://docs.conda.io/en/latest/miniconda.html
      2) run the miniconda installer (100-200Mb). No need to ask for numpy: during the setup script (see step 4)
         you will be asked to create a specific conda environment named JTutils which will have numpy.

3) In Topspin preferences, set [DESTDIR]/JTutils/TSpy as scanned directory
   for python script then restart topspin.

4) run setup\_JTutils in topspin : if report does not point out problem, 
everything should work!

## Remarks
### Old versions of topspin :
Old versions of topspin are using too old version of jython. This version can 
be updated by changing jython.jar file found in TOPSPIN\_INSTALL\_DIR/classes/lib/
with one more recent. Be aware that jython.jar files on jython website also 
depend on java version. For example, only jython version up to 2.5 can be 
installed on topspin 2.1 since higher versions of jython (2.7) require java 7 
while topspin 2.1 only provides java 6.

### Jython version \< 2.7
For jython versions \<2.7, argparse module is not provided as standard module. 
Scripts can run without but adding argparse is easy :
- simply copy argparse.py file found at https://github.com/ThomasWaldmann/argparse/ in 
\<TOPSPIN\_DIR\>/jython/Lib/ directory.
