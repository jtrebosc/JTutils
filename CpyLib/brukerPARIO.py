# -*- coding: utf-8 -*-
# this brukerIO Cpython library requires numpy to manipulate arrays
# in particular this is true for reading 2D processed data that
# have submatrix ordering (xdim)
# therefore this cannot be used directly in topspin python scripts

# Copyright Julien TREBOSC 2011, 2012
# Licence:
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>


# note on processed data:
# management of nD data is quite complex given the acquisition possibilities:
# FnMODE/MC2: QF, QSEQ, TPPI, States, States-TPPI or Echo-Antiecho
# after FT along 1 or 2 dimensions will produce different sets
# of files (2rr, 2ii, 2ir etc....)
# Detailled description is in procref.pdf file (see xfb command description)
# Processing parameters to check or set are FT_mod and FnMODE or MC2
# According to topspin manual :
# FnMODE          |   Fourier transform mode  |   status FT_mod
# undefined       |   according to MC2
# QF              |   forward, quad, real     |   fqc
# QSEQ            |   forward, quad, real     |   fqr
# TPPI            |   forward, single, real   |   fsr
# States          |   forward, quad, complx   |   fqc
# States-TPPI     |   forward, single, complx |   fsc
# Echo-AntiEcho   |   forward, quad, complx   |   fqc
#
# FT_mod determines the data storage and type (time or frequency) in each dim
# 0 : nothing done: Re and Im are stored in subsequent array cells
# 1 : isr inverse FT of single (X) channel storing real part only:
# 2 : iqc inverse FT of quadrature (XY) channel storing complexe:
# 3 : iqr inverse FT of quadrature (XY) channel storing real part only:
# 4 : fsc forward FT of single (X) channel storing complexe:
# 5 : fsr forward FT of single (X) channel storing real part only
# 6 : fqr forward FT of quadrature (XY) channel storing real part only
# 7 : fqc forward FT of quadrature (XY) channel storing complexe
# 8 : isc inverse FT of single (X) channel storing complexe
#

from __future__ import division, print_function
import sys
import os.path
import os
import re
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

pyver = sys.version
# print("python version: " + pyver)

if pyver < "2.7":
    print("python version: " + pyver)
    raise Exception("current version %s. version >= 2.7 required!" % (pyver,))

# I need to rewrite this function in a cleaner way
def splitprocpath(path):
        """Extract [name, expno, procno, dir, user] from path to procno folder

        --- Arguments ---
        path: the path to split as string with folder separator based on os.path.split method

        --- returned value ---
        a list with [name, expno, procno, dir, [user]] elements as required to instantiate a dataset object
        user element may be absent for topspin version > 3

        --- Raised Error ---
        raise ValueError if string cannot be splitted occording to Bruker path structure 
        
        """
        (directory, user, name, expno, procno) = ('', '', '', '', '')
        # make path absolute and normalised
        path = os.path.abspath(path)
        (path, procno) = os.path.split(path)
        (path, tmp) = os.path.split(path)
        if tmp != "pdata":
            raise ValueError("path %s does not seem a valid procno path" % (path,))
        (path, expno) = os.path.split(path)
        (path, name) = os.path.split(path)
        path_list = []
        (drive, tmp) = os.path.splitdrive(path)
        # to be tested on Windows
        while path != drive + os.sep:
            (path, tmp) = os.path.split(path)
            path_list.insert(0, tmp)
        path_list.insert(0, path) # add the drive and root to path_list
        if len(path_list) >= 3 and path_list[-1] == "nmr" and path_list[-3] == "data":
            # we are in version <3
            path_list.pop()  # drops the nmr folder
            user = path_list.pop()
            path_list.pop()  # drops the data folder
            directory = os.path.join(*path_list)
            directory = os.path.normpath(directory)
        else:  # this is version 3 without data/user/nmr format
            directory = os.path.join(*path_list)
            directory = os.path.normpath(directory)
        if user == '':
            for i in [name, expno, procno, directory]:
                if i == '':
                    raise ValueError("path %s does not seem a valid procno path" % (path,))
            return [name, expno, procno, directory]
        else:
            for i in [name, expno, procno, directory, user]:
                if i == '':
                    raise ValueError("path %s does not seem a valid procno path" % (path,))
            return [name, expno, procno, directory, user]


def getlistfilefullname(filename, type='PP'):
    """ You provide a list filename (taken from a VCLIST name parameter for
    example), and the kind of file it is (see below for type) then this
    function searches in topspin standard and user defined folders  for the
    filename and returns its full pathname.
    'type' should be in the list:
    BASLPNTS  : points definition for baseline correction
    VC        : variable counter list file
    PP        : pulse program file
    STRUCTURE : structure file
    PEAKRNG   : peak range file
    VD        : variable delay list file
    INTRNG    : integral region file
    PY        : python program file
    VT        : variable temperature file
    SHAPE     : shape file
    PAR       : parameter file
    F1        : F1
    CLEVELS   : contour level definition file
    MAC       : macro file
    SCL       : ????
    SP        : ????
    INT2DRNG  : ????
    CPD       : CPD program file
    REG       : ????
    BASE_INFO : ????
    GP        : gradient program file
    AU        : AU program file
    PEAKLIST  : peaklist file
    VP        : variable pulse list file
    DS        : ????
    PHASE     : ????
    VA        : variable amplitude file
    """

    allowedTypes = ["BASLPNTS",
                    "VC",
                    "PP",
                    "STRUCTURE",
                    "PEAKRNG",
                    "VD",
                    "INTRNG",
                    "PY",
                    "VT",
                    "SHAPE",
                    "PAR",
                    "F1",
                    "CLEVELS",
                    "MAC",
                    "SCL",
                    "SP",
                    "INT2DRNG",
                    "CPD",
                    "REG",
                    "BASE_INFO",
                    "GP",
                    "AU",
                    "PEAKLIST",
                    "VP",
                    "DS",
                    "PHASE",
                    "VA",
                    ]

    if type not in allowedTypes:
        raise NameError("unknown type: should be in %s" % str(allowedTypes))
    nmrhome = os.getenv("XWINNMRHOME")
    userparamdir = os.getenv("JAVA_LOGDIR")
    userparamfile = userparamdir + "/parfile-dirs.prop"
    try:
        f = open(userparamfile, 'r')
    except:
        raise IOError("Cannot open " + userparamfile)

    for i in f.readlines():
        m = re.match(type + "_DIRS=(.*)", i)
        if m:
            break
    vcdirlist = m.group(1).split(';')
    fullname = ''
    for i in vcdirlist:
        # check whether relative or full name is used,
        # if relative then complete to full path name
        if i[0] != '/':
            i = nmrhome + "/exp/stan/nmr/" + i+"/" + filename
        if os.path.exists(i):
            # MSG(i)
            fullname = i
            break
    if fullname == '':
        return None
    return fullname

"""
AQSEQ contains an integer that codes the dimension (F1, F2, F3 as
      they appear in eda and refering to acqus, acqu2s, acqu3s
      etc...) storage order.
For 2D there is no need for it. the value is always 0
For 3D one has the following order:
    0: F3F2F1
    1: F3F1F2
For 4D : not checked on real dataset but my guess
    0: F4F3F2F1
    1: F4F3F1F2
    2: F4F2F3F1
    3: F4F2F1F3
    4: F4F1F3F2
    5: F4F1F2F3
For 5D nd larger only natural order is allowed : 
    0: F5F4F3F2F1
If AQSEQ is not set (-1 ??? or missing key ?) then processing parameter AQORDER is used
"""
# permutations dict(dimension: dict(AQSEQ: [dimension order]))
# where dimension as int is the spectrum dimensionality (2D, 3D, .... nD)
# and AQSEQ as int is the AQSEQ order (0, 1, 2...)
_AQSEQ_permutations = { 3: {0: [ 0, 1], 1: [1, 0]}, 
                4: {0: [ 0, 1, 2], 1: [1, 0, 2], 2: [0, 2, 1], 3: [2, 0, 1], 4: [1, 2, 0], 5: [2, 1, 0]}
              }

class dataset:
    """
    class to handle bruker datasets
    instanciation uses bruker style:
    a tuple containing [name, expno, procno, dir, user]
    variables:
    dataset: bruker way of defining datasets in a list [name, expno,
                          procno, dir [, user]]
    version: 2 for topspin versions <3 and 3 for topspin versions >= 3
    bytencP: processed data byte encoding of dataset
    bytencA: raw data byte encoding of dataset
    dimA: int with dimension of acqusition (1/2/3 for 1D/2D/3D)
    dimP: int with dimension of processing (1/2/3 for 1D/2D/3D)

    valid datasets must at least have acqu file present and proc,
                  else raise error
    haveRawData is True if fid or ser file is present
    haveProcData is True if 1r, 2rr or 3rr file is present

    method:
    * =returnacqpath()                        returns "string"
    * =returnprocpath()                       returns "string"
    * =readacqpar("param", status=True(|False), dimension=1(|2|3))
                                              returns converted value (str, bool, float, int)
    * =readprocpar("param", status=True(|False), dimension=1(|2|3))
                                              returns converted value (str, bool, float, int)
    * =writeacqpar("param", value="0", status=True(|False), dimension=1(|2|3))
                                              returns nothing
    * =writeprocpar("param", value="0", status=True(|False), dimension=1(|2|3))
                                              returns nothing
    * =getdigfilt()                           returns int
    * =audita_times                           returns acquisition times from audita.txt file
                                                      as tuple(start_time, end_time, exp_time)
                times are datetime and timedelta instances
                Note that exp_time is not necessarily end-start as subsequent go command 
                may have produced the dataset
    TODO:
    - read title
    - parser for status pulseprogram
    - dictionary: parameter/parameter meaning/value
    - write part: write parameter/fid or ser file/ processed spectra...
    """

    def __init__(self, dset=['', '', '', '', '']):
        self.dataset = dset
        # if list is 5 arguments then it's topspin version < 3
        # else it's topspin version 3
        if len(dset) == 5:
            self.version = 2
        elif len(dset) == 4:
            self.version = 3
        else:
            raise ValueError('dataset %s has length %d' % 
                              (','.join(dset), len(dset)))
        self.MC2_list = ["QF", "QSEQ", "TPPI", "States", "States-TPPI", "echo-antiecho", "QF(no-frequency)"]
        if not os.path.exists(self.returnacqpath()):
            raise IOError("Wrong dataset:\n" + self.returnacqpath() +
                          " does not exist!!")
        if not os.path.exists(self.returnacqpath() + 'acqu'):
            raise IOError("Wrong dataset:\n" + self.returnacqpath() + 'acqu' +
                          " does not exist!!")
        if not os.path.exists(self.returnprocpath() + 'proc'):
            raise IOError("Wrong dataset:\n" + self.returnprocpath() + 'proc' +
                          " does not exist!!")
        try:
            self.dimA = self.readacqpar("PARMODE", False) + 1
            self.dimA = self.readacqpar("PARMODE", False) + 1
        except TypeError:
            raise IOError("Wrong dataset:\n" + self.returnacqpath() + 'acqu' +
                          " is not readable")
        try:
            self.dimP = self.readprocpar("PPARMOD", False) + 1
            self.dimP = self.readprocpar("PPARMOD", False) + 1
        except TypeError:
            raise IOError("Wrong dataset:\n" + self.returnprocpath() + 'proc' +
                          " is not readable")

        # treat acquisition parameters bytord and haveRawData
        if self.dimA == 1:
            path = self.returnacqpath() + "fid"
            if os.path.exists(path):
                self.haveRawData = True
            else:
                self.haveRawData = False
        else:
            path = self.returnacqpath() + "ser"
            if os.path.exists(path):
                self.haveRawData = True
            else:
                self.haveRawData = False
        # --------------------------------------------------
        # DTYPA: 0 for integer on 4 bytes (int32)
        #        1 for float on 4 bytes (float32): never used
        #        2 for float on 8 bytes (float64)
        # --------------------------------------------------
        brukDTYP = ['i4', 'f4', 'f8']
        brukBYTORD = ['<', '>']  # bytord 0=little 1=big
        try:
            brukBYTORDA = self.readacqpar("BYTORDA", self.haveRawData)
        except:
            brukBYTORDA = 0
        try:
            BrukDTYPA = self.readacqpar("DTYPA", self.haveRawData)
        except:
            BrukDTYPA = 0

        if brukBYTORDA == 0:
            self.bytencA = 'little'
        else:
            self.bytencA = 'big'
        # treat processing parameters bytord and haveProcData
        if self.dimP == 1:
            path = self.returnprocpath() + "1r"
            if os.path.exists(path):
                self.haveProcData = True
            else:
                self.haveProcData = False
        elif self.dimP == 2:
            path = self.returnprocpath() + "2rr"
            if os.path.exists(path):
                self.haveProcData = True
            else:
                self.haveProcData = False
        elif self.dimP > 2:
            path = self.returnprocpath() + "3rrr"
            if os.path.exists(path):
                self.haveProcData = True
            else:
                self.haveProcData = False
        else:
            self.haveProcData = False

        try:
            brukBYTORDP = self.readprocpar("BYTORDP", self.haveRawData)
        except:
            brukBYTORDP = 0
        try:
            BrukDTYPP = self.readprocpar("DTYPP", self.haveRawData)
        except:
            BrukDTYPP = 0

#        print("proc data stored as %s" % (self.dtypeP, ))
        if brukBYTORDP == 0:
            self.bytencP = 'little'
        else:
            self.bytencP = 'big'

    def returnacqpath(self):
        """
        returns folder pathway where acqu/fid files are stored
                                         (with "/" separators)
        """
        if self.version == 2:
            path = "%s/data/%s/nmr/%s/%s/" % (self.dataset[3], self.dataset[4],
                                              self.dataset[0], self.dataset[1])
            return path
        elif self.version == 3:
            path = "%s/%s/%s/" % (self.dataset[3], self.dataset[0],
                                  self.dataset[1])
            return path
        else:
            return ""

    def returnprocpath(self):
        """
        returns folder pathway where proc/1r/2rr... files are stored
                                           (with "/" separators)
        """
        if self.version == 2:
            path = "%s/data/%s/nmr/%s/%s/pdata/%s/" % (
                    self.dataset[3], self.dataset[4], self.dataset[0],
                    self.dataset[1], self.dataset[2])
            return path
        elif self.version == 3:
            path = "%s/%s/%s/pdata/%s/" % (
                    self.dataset[3], self.dataset[0], self.dataset[1],
                    self.dataset[2])
            return path
        else:
            return ""

    def writeacqpar(self, param, value, status=True, dimension=1):
        """
        Write parameter "param" to acqu/acqus/acqu2/acqu2s
        If status=True writes "status" parameter (default)
        Writes in file corresponding to dimension (default 1)
             acqu or acqus if dimension=1
             acqu'n' or acqu'n's if dimension='n'
        Returns True if success or False if parameter is not found.
        User must convert the parameter to string
        Can write arrayed parameter with parameter array name and index
            in the array separated by a space
        e.g.: "P 1", "D 0"
        """

        if dimension == 1:
            name = 'acqu'
        else:
            name = 'acqu'+str(dimension)
        if status is True:
            name += 's'

        path = self.returnacqpath() + name

        if not os.path.exists(path):
            raise FileNotFoundError("Parameter file %s not found: is dimension %d correct ?" % (name, dimension))
        return self._writepar2(path, param, value)

    def writeprocpar(self, param, value, status=True, dimension=1):
        """
        writes parameter "param" from proc/procs/proc2/proc2s
        if status=True reads "status" parameter (default)
        writes in file corresponding to dimension (default 1)
                proc or procs if dimension=1
            proc2 or proc2s if dimension=2
        returns True if success or False if parameter is not found.
        User must convert the parameter to string
        """

        if dimension == 1:
            name = 'proc'
        else:
            name = 'proc' + str(dimension)
        if status is True:
            name += 's'

        path = self.returnprocpath() + name

        if not os.path.exists(path):
            raise FileNotFoundError("Parameter file %s not found: is dimension %d correct ?" % (name, dimension))
        return self._writepar2(path, param, value)

    def readacqpar(self, param, status=True, dimension=1):
        """
        Reads parameter "param" from acqu/acqus/acqu2/acqu2s
        If status=True reads "status" parameter (default)
        Reads in file corresponding to dimension (default 1)
               acqu or acqus if dimension=1
               acqu2 or acqu2s if dimension=2
        Returns parameter as string or None if parameter is not found.
        User must convert the parameter type himself if needed
        Can extract arrayed parameter with parameter array name and index
             in the array separated by a space
        e.g.: "P 1", "D 0"
        """

        if dimension == 1:
            name = 'acqu'
        else:
            name = 'acqu' + str(dimension)
        if status is True:
            name += 's'

        path = self.returnacqpath() + name

        if not os.path.exists(path):
            raise FileNotFoundError("Parameter file %s not found: is dimension %d correct ?" % (name, dimension))
        return self._readpar2(path, param)

    def readprocpar(self, param, status=True, dimension=1):
        """
        reads parameter "param" from proc/procs/proc2/proc2s
        if status=True reads "status" parameter (default)
        reads in file corresponding to dimension (default 1)
                proc or procs if dimension=1
            proc2 or proc2s if dimension=2
        returns parameter as string or None if parameter is not found.
        User must convert the parameter type himself if needed
        """

        if dimension == 1:
            name = 'proc'
        else:
            name = 'proc' + str(dimension)
        if status is True:
            name += 's'

        path = self.returnprocpath() + name

        if not os.path.exists(path):
            raise FileNotFoundError("Parameter file %s not found: is dimension %d correct ?" % (name, dimension))
        return self._readpar2(path, param)

    def _readpar(self, path, param):
        """
        Reads parameter "param" from JCAMPDX file specified in path
        Returns parameter as string or None if parameter is not found.
        User must convert the parameter type himself if needed
        Can extract arrayed parameter with parameter array name and index
                                  in the array separated by a space
        e.g.: "P 1", "D 0"
        """
        value = None
        t = param.split(' ')
        [searchString, pindex] = [-1, -1]
        if len(t) > 1:
            [searchString, pindex] = t
        else:
            searchString = t[0]
        try:
            f = open(path, "r")
        except:
            raise IOError("Cannot open " + path)

        try:
            ls = f.readlines()
        except:
            raise IOError("Error reading" + path)
        f.close()
        found = 0
        for index in range(0, len(ls)-1):
            line = ls[index].strip()
            if line.find("##$" + searchString + "=") > -1:
                # case of non array
                if int(pindex) == -1:
                    [tmp, value] = line.split('=', 1)
                    value = value.strip(" <>")
                    found = 1
                    break
                # case of array
                else:
                    arraylist = []
                    matchres = re.search(r"\(0\.\.([0-9]+)\)", line)
                    if matchres:
                        maxindex = int(matchres.group(1))
                        # print("maxindex="+str(maxindex))
                    else:
                        raise ValueError("Sorry, " + searchString +
                              " doesn't appear to be an array")

                    [tmp, arrayed] = line.split(')')
                    if not arrayed == '':
                        arraylist = arrayed.strip().split(' ')
                    i = 1
                    line = ls[index + i].strip()
                    while not line.startswith('#'):
                        arraylist = arraylist + line.split(' ')
                        i = i+1
                        line = ls[index + i].strip()
                    break
        if int(pindex) > -1:
            if int(pindex) <= int(maxindex):
                value = arraylist[int(pindex)]
                found = 1
            else:
                raise ValueError("Sorry array list index %s is beyond MAX index %d: " % (pindex, maxindex))

        if not found:
            raise ValueError("Sorry, couldn't find param '" + searchString + "'")
        return value

    def _writepar(self, path=None, param=None, value=""):
        """
        changes parameter "param" to value in JCAMPDX file specified in path
        returns parameter as string or None if parameter is not found.
        User must convert the parameter type himself if needed
        Can extract arrayed parameter with parameter array name and index in
                the array separated by a space
        e.g.: "P 1", "D 0"
        syntax:
        #$STRING= <string>
        #$NUMBER= number
        #$ARRAY= (0..MAXINDEX)
        0 0 0 0 0 0 0 0 0 0 0 0 (max character 71 column, but can extend beyond
                if last value start on column 71)
        """
        found = None
        # split the param. If more than one split then it's an array with
        # an index else it's a scalar
        t = param.split(' ')
        [searchString, pindex] = [-1, -1]
        if len(t) > 1:
            [searchString, pindex] = t
        else:
            searchString = t[0]
        try:
            f = open(path, "r")
        except:
            raise IOError("cannot open " + path)

        ls = f.readlines()
        f.close()
        # look for param in ls then parse value or array
        for index in range(0, len(ls)-1):
            line = ls[index]
            if line.find("##$" + searchString + "=") > -1:
                # case of non array
                if pindex == -1:
                    if line.find('<') >= 0:
                        value = "<"+value+">"
                    line = "##$"+searchString+"= "+value+"\n"
                    ls[index] = line
                    found = 1
                    break
                # case of array
                else:
                    arraylist = []
                    # maxindex contains max index from #$ARRAY= (0..MAXINDEX)
                    matchres = re.search(r"\(0\.\.([0-9]+)\)", line)
                    if matchres:
                        maxindex = int(matchres.group(1))
                        # print("maxindex="+str(maxindex))
                    else:
                        raise ValueError("Search string %s is not an array" % (searchString,))

                    # read all array values
                    i = 1
                    line = ls[index + i].strip()
                    while not line.startswith('#'):
                        arraylist = arraylist + line.split(' ')
                        i = i+1
                        line = ls[index + i].strip()
                    max_i = i
                    if (len(arraylist) > int(pindex)):
                        found = 1
                    # delete lines index+1 to index+i-1 included
                    del ls[index + 1:index + max_i]
                    # change the correponding value
                    if int(pindex) <= int(maxindex):
                        arraylist[int(pindex)] = value
                        arraystring = " ".join(arraylist)
                        maxchar = 72
                        i = 1
                        arrayst = []
                        while len(arraystring) > maxchar:
                            splitindex = arraystring.rfind(" ", 0, maxchar)
                            arrayst.append(arraystring[0:splitindex] + "\n")
                            arraystring = arraystring[splitindex:].lstrip()
                            i = i+1
                        arrayst.append(arraystring+"\n")
                        # at this point one need to insert i lines after index
                        for j in range(i):
                            ls.insert(index+1+j, arrayst[j])
                    else:
                        raise ValueError("Array parameter index of %s invalid. Max index is %d" % (searchString, maxindex))
                    break

        if not found:
            raise ValueError("Parameter %s not found in %s" % (searchString, path))

        # write the file back
        try:
            f = open(path, "w")
        except:
            raise IOError("cannot open " + path)
        f.write(''.join(ls))
        f.close()
        return True

    def _readpar2(self, path, param):
        """
        Reads parameter "param" from JCAMPDX file specified in path
        Parameter conversion is done between numeric (int or float), string or boolean
        Can extract arrayed parameter with parameter array name and index
                                  in the array separated by a space
        e.g.: "P 1", "D 0"
        """
        [searchString, pindex] = [-1, -1]
        t = param.split(' ')
        searchString = t[0]
        if len(t) > 1:
            pindex = int(t[1])
        try:
            f = open(path, "r")
        except:
            raise IOError("Cannot open file %s" % (path,))
        try:
            ls = f.readlines()
        except:
            raise IOError("Cannot read lines in file %s." % (path,))
        f.close()

        for index in range(0, len(ls)-1):
            line = ls[index].strip()
            # if line contains a parameter (starts with ##$)
            if line.startswith("##$" + searchString + "="): # parameter found
                _, value_field = line.split('=', 1)
                value_field = value_field.strip()
                if value_field.startswith("("): # array:
                    if pindex == -1:
                        raise IndexError("Parameter %s is an array. An index is required"%(searchString,))
                    # get number of array elements
                    tmp = value_field.split('..')
                    array_start = int(tmp[0][1:]) # first element removing starting (
                    array_end = int(tmp[1][:-1]) # second element removing trailing )
                    array_size = array_end - array_start + 1

                    array_lines = []
                    array_i = 1
                    line =  ls[index+array_i].strip()
                    while not line.startswith('#'): # join all subsequent array lines
                        array_lines.append(line)
                        array_i += 1
                        line =  ls[index+array_i]
                    if len(array_lines) == 0: 
                        raise ValueError("%s is inconsistent JCAMPDX file. Could not parse %d array value for parameter %s" % 
                                            (path, array_size, searchString) )
                    value_line = ' '.join(array_lines)

                    # what is array ? numeric, boolean or string ?
                    if value_line.startswith('<'): #string list
                        value_line = value_line[1:-1]  # strip leading and trailing < >
                        value_array = value_line.split('> <') # assumes only one space between 2 strings > <
                    elif ('yes' in value_line) or ('no' in value_line): # boolean list
                        value_array = [val == 'yes' for val in value_line.split()]
                    else: # hopefully numeric value which is returned as float or int
                        if 'e' in value_line or '.' in value_line or 'inf' in value_line:
                            value_array = [float(val) for val in value_line.split()]
                        else:
                            value_array = [int(val)   for val in value_line.split()]
                    try :
                        return value_array[pindex]
                    except IndexError:
                        raise IndexError("Parameter %s has no index %d (max=%d) in %s" % (searchString, pindex, array_end, path))
                elif 'yes' in value_field or 'no' in value_field:
                    return value_field == 'yes'
                elif value_field.startswith('<'):
                    return value_field[1:-1] # strips < >
                elif 'e' in value_field or '.' in value_field or 'inf' in value_field:
                    return float(value_field)
                else:
                    return int(value_field)
        # reach end of file
        raise ValueError("Parameter %s not found in %s" % (searchString, path))

    def _writepar2(self, path=None, param=None, value=""):
        """
        changes parameter "param" to value in JCAMPDX file specified in path
        returns parameter as string or None if parameter is not found.
        Parameter type is checked. TypeError is raise if type does not match
        Can extract arrayed parameter with parameter array name and index in
                the array separated by a space
        e.g.: "P 1", "D 0"
        syntax:
        #$STRING= <string>
        #$NUMBER= number
        #$ARRAY= (0..MAXINDEX)
        0 0 0 0 0 0 0 0 0 0 0 0 (max character 71 column, but can extend beyond
                if last value start on column 71)
        """
        # split the param. If more than one split then it's an array with
        # an index else it's a scalar
        [searchString, pindex] = [-1, -1]
        t = param.split(' ')
        searchString = t[0]
        if len(t) > 1:
            pindex = int(t[1])
        try:
            f = open(path, "r")
        except:
            raise IOError("Cannot open " + path)

        ls = f.readlines()
        f.close()

        found = False
        for index in range(0, len(ls)-1):
            line = ls[index].strip()
            # if line contains a parameter (starts with ##$)
            if line.startswith("##$" + searchString + "="): # parameter found
                found = True
                par_key, value_field = line.split('=', 1)
                value_field = value_field.strip()
                if value_field.startswith("("): # array:
                    if pindex == -1:
                        raise IndexError("Parameter %s is an array. An index is required"%(searchString,))
                    # get number of array elements
                    tmp = value_field.split('..')
                    array_start = int(tmp[0][1:]) # first element removing starting (
                    array_end = int(tmp[1][:-1]) # second element removing trailing )
                    array_size = array_end - array_start + 1

                    array_lines = []
                    array_i = 1
                    line =  ls[index+array_i].strip()
                    while not line.startswith('#'): # join all subsequent array lines
                        array_lines.append(line)
                        array_i += 1
                        line =  ls[index+array_i].strip()
                    if len(array_lines) == 0: 
                        raise ValueError("%s is inconsistent JCAMPDX file. Could not parse %d array value for parameter %s" % 
                                            (path, array_size, searchString) )
                    value_line = ' '.join(array_lines)

                    # what is array ? numeric, boolean or string ?
                    if value_line.startswith('<'): #string list
                        value_type = str
                        if value_type != type(value):
                            raise TypeError("Type of provided value (%s) does not match parameter type (%s)" 
                                            % (str(type(value)), str(value_type)))
                        value_line = value_line[1:-1]  # strip leading and trailing < >
                        value_array = value_line.split('> <') # assumes only one space between 2 strings > <
                        value_array = ['<' + val + '>' for val in value_array] # reconstruct the array with <strings>
                        value = '<' + value + '>'
                    elif ('yes' in value_line) or ('no' in value_line): # boolean list
                        value_type = bool
                        if value_type != type(value):
                            if value != 'yes' and value != 'no':
                                raise TypeError("Type of provided value (%s) does not match parameter type (%s)" 
                                                % (str(type(value)), str(value_type)))
                        value_array = value_line.split()
                        if value is True : value = 'yes'
                        if value is False : value = 'no'
                    else: # hopefully numeric value which is returned as float or int : 
                        # ambiguity when float represented as int e.g 3 instead of 3.0
                        # you need to know if int or float
                        if 'e' in value_line or '.' in value_line or 'inf' in value_line:
                            value_type = float
                            if ('float' not in str(type(value)) ) and ('int' not in str(type(value))):
                                raise TypeError("Type of provided value (%s) does not match parameter type (float, int)" 
                                                % (str(type(value)), ))
                        else:
                            value_type = int
                            if ('float' not in str(type(value)) ) and ('int' not in str(type(value))):
                                raise TypeError("Type of provided value (%s) does not match parameter type (float or int)" 
                                                % (str(type(value)), ))
                        value_array = value_line.split()
                        value = str(value)
                    try:
                        value_array[pindex] = value
                    except IndexError:
                        raise IndexError("Parameter %s has no index %d (max=%d) in %s" % (searchString, pindex, array_end, path))
                    
                    # pack array in lines of maximum length 80 characters
                    value_lines = []
                    tmp_line = ""
                    for val in value_array:
                        if len(val) + 1 + len(tmp_line) < 71:
                            tmp_line += ' ' + val
                        else : 
                            value_lines.append(tmp_line + '\n')
                            tmp_line = val
                    value_lines.append(tmp_line + '\n')

                    # delete existing entry and insert new lines
                    del ls[index + 1:index + array_i]
                    for j in range(len(value_lines)):
                        ls.insert(index+1+j, value_lines[j])
                elif 'yes' in value_field or 'no' in value_field:
                    if type(value) is not bool and value != 'yes' and value != 'no':
                            raise TypeError("Type of provided value (%s) does not match parameter type (bool, 'yes', 'no')" 
                                            % (str(type(value)), ))
                    if value is True: value = 'yes'    
                    if value is False: value = 'no'    
                    value_field = value
                    ls[index] = par_key  + '= ' + value_field + "\n"
                elif value_field.startswith('<'):
                    if type(value) is not str:
                        raise TypeError("Type of provided value (%s) does not match parameter type (str)" 
                                        % (str(type(value)), ))
                    value_field = '<' + value + '>'
                    ls[index] = par_key  + '= ' + value_field + "\n"
                elif 'e' in value_field or '.' in value_field or 'inf' in value_field:
                    if ('float' not in str(type(value)) ) and ('int' not in str(type(value))):
                        raise TypeError("Type of provided value (%s) does not match parameter type (float, int)" 
                                        % (str(type(value)), ))
                    value_field = str(value)
                    ls[index] = par_key  + '= ' + value_field + "\n"
                else:
                    if ('float' not in str(type(value)) ) and ('int' not in str(type(value))):
                        raise TypeError("Type of provided value (%s) does not match parameter type (float, int)" 
                                        % (str(type(value)), ))
                    value_field = str(value)
                    ls[index] = par_key  + '= ' + value_field + "\n"
        # reach end of file of parameter is found
        if not found:
            raise ValueError("Parameter %s not found in %s" % (searchString, path))
        # write the file back
        try:
            f = open(path, "w")
        except:
            raise IOError("Cannot open " + path)
        f.write(''.join(ls))
        f.close()
        return True

    def getdigfilt(self):
        """
        returns the number of complex points that corresponds to
        digital filter artifact in a fid/ser file
        """
        tabgrpdly = {
            10:     {
                2: 44.7500,
                3: 33.5000,
                4: 66.6250,
                6: 59.0833,
                8: 68.5625,
                12: 60.3750,
                16: 69.5313,
                24: 61.0208,
                32: 70.0156,
                48: 61.3438,
                64: 70.2578,
                96: 61.5052,
                128: 70.3789,
                192: 61.5859,
                256: 70.4395,
                384: 61.6263,
                512: 70.4697,
                768: 61.6465,
                1024:    70.4849,
                1536: 61.6566,
                2048: 70.4924,
                },
            11:    {
                2: 46.0000,
                3: 36.5000,
                4: 48.0000,
                6: 50.1667,
                8: 53.2500,
                12: 69.5000,
                16: 72.2500,
                24: 70.1667,
                32: 72.7500,
                48: 70.5000,
                64: 73.0000,
                96: 70.6667,
                128: 72.5000,
                192: 71.3333,
                256: 72.2500,
                384: 71.6667,
                512: 72.1250,
                768: 71.8333,
                1024: 72.0625,
                1536: 71.9167,
                2048: 72.0313
                },
            12:     {
                2: 46.3110,
                3: 36.5300,
                4: 47.8700,
                6: 50.2290,
                8: 53.2890,
                12: 69.5510,
                16: 71.6000,
                24: 70.1840,
                32: 72.1380,
                48: 70.5280,
                64: 72.3480,
                96: 70.7000,
                128: 72.5240,
                192: 0.0000,
                256: 0.0000,
                384: 0.0000,
                512: 0.0000,
                768: 0.0000,
                1024:    0.0000,
                1536: 0.0000,
                2048: 0.0000
                },
            13:     {
                2: 2.75,
                3: 2.8333333333333333,
                4: 2.875,
                6: 2.9166666666666667,
                8: 2.9375,
                12: 2.9583333333333333,
                16: 2.96875,
                24: 2.9791666666666667,
                32: 2.984375,
                48: 2.9895833333333333,
                64: 2.9921875,
                96: 2.9947916666666667
                }
            }

        dspfirm = self.readacqpar("DSPFIRM", True)
        digtyp = self.readacqpar("DIGTYP", True)

        decim = int(self.readacqpar("DECIM", True)) # decim can be float ?
        dspfvs = self.readacqpar("DSPFVS", True)
        digmod = self.readacqpar("DIGMOD", True)

        if digmod == 0:
            return 0
        if dspfvs >= 20:
            return self.readacqpar("GRPDLY", True)
        if ((dspfvs == 10) | (dspfvs == 11) |
                             (dspfvs == 12) | (dspfvs == 13)):
            return tabgrpdly[dspfvs][decim]
        if dspfvs == 0:
            return 0.0
        if dspfvs == -1: # For FIDs gnereated by genser of genfid for example
            return 0.0

        raise NameError("DSPFVS="+str(dspfvs)+" not yet implemented")


    def guess_proc_filenames(self, domains):
        """Tries to guess the filenames depending on transforms done for further topspin processing

            Depending on number of dimension, Fourier Transform steps, MC2 value, the function will return
            a list of names required to further process the data within topspin
            2D: with QF 2rr and 2ii always, with HC 2rr and 2ir if F1 not processed, all quadrant otherwise with name 2[F2 i/r][F1 i/r]
                MC2 = QF(f1) :
                    FT(t1, t2)
                    FT(no,no) ->  2rr, 2ii
                    FT(no,xx) -> 2rr, 2ii
                    FT(xx, no) -> 2rr, 2ii
                    FT(xx, fqc) -> 2rr, 2ii
                MC2 = States[-TPPI] (f1) with hypercomplex acquisition
                    FT(t1, t2)
                    FT(no, no) -> 2rr, 2ir
                    FT(no,xx) -> 2rr, 2ir
                    FT(xx, no) -> 2rr, 2ir, 2ri, 2ii
                    FT(xx, xx) -> 2rr, 2ir, 2ri, 2ii
            3D:
                Note that topspin can only process as tf3 first then tf2 and tf1 in either order
                and one cannot rephase a dimension once the next is transformed (unless HT is done)
                tfx (x=1, 2, 3) does FT without evaluation of FT_mod
                MC2 = States[-TPPI](t2) / States[-TPPI](t1) : hypercomplex acquisition in both dimensions
                    FT(t1, t2, t3)
                    FT(no, no,no) ->  impossible as FT always done with ftnd or ft3, ft2 ft1
                    FT(no, no,fqc) ->  3rrr, 3irr 
                    FT(no, fsc, fqc) -> 3rrr, 3rir (imaginary part of F3 is discarded unless hilbert transform was done afterwards)
                    FT(fsc, no, fqc) -> 3rrr, 3rri
                    FT(fsc, fsc, fqc) -> 3rrr, 3rri or 3rir depending if tf2 or tf1 was first
                    after 3D FT, Hilbert Transform (HT) in F3 adds 3irr, in F2 adds 3rir but there are still some missing octants like 3iii, 3iir, 3iri, 3rii.
                    A priori, no inverse transform is feasible
                MC2 = QF(t2) / States(t1)
                    FT(t1, t2, t3)
                    FT(no, no,no) ->  impossible as FT always done
                    FT(no, no, fqc) -> 3rrr, 3iii
                    FT(no, fqc, fqc) -> 3rrr, 3iii
                    FT(fqc, no, fqc) -> 3rrr, 3iii, 3rri (3iii ???)
                    FT(fqc, fqc, fqc) -> 3rrr, 3rri (tf3;tf2;tf1) or 3iii (tf3;tf1;tf2)
                MC2 = States(t2) / QF(t1)
                    FT(t1, t2, t3)
                    FT(no, no,no) ->  impossible as FT always done
                    FT(no, no, fqc) -> 3rrr, 3iii
                    FT(no, fqc, fqc) -> 3rrr, 3rir, 3iii (what is 3iii ?)
                    FT(fqc, no, fqc) -> 3rrr, 3iii
                    FT(fqc, fqc, fqc) -> 3rrr, 3iii (tf3;tf2;tf1) or 3rir (tf3;tf1;tf2), 
                MC2 = QF(t2) / QF(t1)
                    FT(t1, t2, t3)
                    FT(no, no,no) ->  impossible as FT always done
                    FT(no, no, fqc) -> 3rrr, 3iii
                    FT(no, fqc, fqc) -> 3rrr, 3iii
                    FT(fqc, fqc, fqc) -> 3rrr, 3iii
            4D:
                Only processing allowed is ftnd and mixed QF/HC not handled by topspin processing
                only 4rrrr is generated by topspin. Separate phasing of processed data is not handled but using Hilbert transform. 
                Topspin displays 2D slice only

            So it's not so easy... The name probably tells about the imaginary part that is available for phasing : 
            
            --- Arguments---
            domains : a list with the 
            --- Returned value ---
            A list with the names of processing files that should exist for further processing
            output:
        """
        return dataset.guess_proc_filenames.__doc__

    def audita_times(self):
        """ 
            Return a tuple with start (datetime), stop (datetime) and 
            length (datetime.timedelta) of an acquisition as read in audita.txt file.
            If start cannot be determined then start=stop and length=0 
            will deal with XWINNMR data
            This function still needs more robust behavior.
        """

    # trail entry (NUMBER, <WHEN>, <WHO>, <WHERE>, <PROCESS>, <VERSION>, <WHAT>)
    # lines with process "go" or "go4" are acquisitions with a "started at" description
    # if acquisition was continued using go instead of zg in topspin one can have a "continue with go"
    # In that case... check for all such posibility
    # popt-ed experiments stored in 2D have not experimental time since no go but wser
    # how to detect 2D popt-ed datasets ?
        from dateutil import parser
        from datetime import datetime, timedelta

        auditname = os.path.join(self.returnacqpath(), 'audita.txt')
        try:
            with open(auditname, 'r') as f:
                lines = f.readlines()
        except IOError:
            # We are probably in a XWINNMR dataset since there is no audita.txt file
            # Then read acqus with DATE -> start and date in comment right after ##ORIGIN -> stop
            # for stop one needs to 
            #    open acqus manually 
            #    search for ##ORIGIN
            #    take next line
            #    parse datetime : dayoftheweek, month3letter, dayofthemonth, HH:MM:SS YYYY 
            # no tzinfo available
            return (0, 0, 0)
        in_trail = False
        audit_trail = []
        for line in lines:
            if line.startswith('##TITLE=') :
                _, version = line.split(',')
                version = version.upper()
            if line.startswith('##') and in_trail == True :
                break
            elif line.startswith('##AUDIT TRAIL'):
                elts = line[line.index("(")+1:line.index(")")].split(', ')
                in_trail = True
                continue
            elif in_trail == True:
                if line.startswith('$$'):
                    continue
                audit_trail.append(line)
                 
        cur = ''.join(audit_trail).strip()
        time_list = []
        # note that XWINNMR has no audita.txt file so we shouldn't reach that point in that case
        if 'TOPSPIN' in version and '1.2' in version:
            ##AUDIT TRAIL=  $$ (NUMBER, WHEN, WHO, WHERE, WHAT)
            while len(cur) > 2:
                if cur.startswith('('):
                    cur = cur[1:]
                    number, cur = cur.split(",",1)
                    when, cur = cur.split(",",1)
                    when = when.strip("<>")
                    who, cur = cur.split(",",1)
                    who = who.strip("<>")
                    where, cur = cur.split(",",1)
                    where = where.strip("<>")
                    what, cur = cur.split(">)",1)
                    how = 'undefined'
                    if 'continue with go' in what :
                        how = 'continue with go'
                    if 'created by zg' in what:
                        how = 'created by zg'
                    if 'undefined' not in how:
                        what = what.strip("<>\n\r \t")
                        try:
                            when =  parser.parse(when)
                        except parser.ParserError:
                            # sometimes tzdata is not standard +100 instead of +0100
                            # so try to fix it
                            import re
                            when = re.sub("\+([1-9])", r'+0\1', when)
                            when =  parser.parse(when)
                        # for topspin 1.2 start time is stored in DATE
                        start = datetime.fromtimestamp(self.readacqpar('DATE', status=True, dimension=1),
                                                        tz=when.tzinfo)

                        time_list.append({'number': number, 'process': 'undefined',
                                               'start': start, "stop": when, 
                                               'how': how})
                    cur = cur.strip()
        elif 'TOPSPIN' in version and '1.3' in version:
            ##AUDIT TRAIL=  $$ (NUMBER, WHEN, WHO, WHERE, VERSION, WHAT)
            while len(cur) > 2:
                if cur.startswith('('):
                    cur = cur[1:]
                    number, cur = cur.split(",",1)
                    when, cur = cur.split(",",1)
                    when = when.strip("<>")
                    who, cur = cur.split(",",1)
                    who = who.strip("<>")
                    where, cur = cur.split(",",1)
                    where = where.strip("<>")
                    version, cur = cur.split(",",1)
                    version = version.strip("<>")
                    what, cur = cur.split(">)",1)
                    how = 'undefined'
                    if 'continue with go' in what :
                        how = 'continue with go'
                    if 'created by zg' in what:
                        how = 'created by zg'
                    if 'undefined' not in how: # we found a record with date information
                        what = what.strip("<>\n\r \t")
                        when =  parser.parse(when) 
                        # for topspin 1.3 start time is stored in DATE
                        start = datetime.fromtimestamp(self.readacqpar('DATE', status=True, dimension=1),
                                                        tz=when.tzinfo)# use same tzinifo offset as in when
                        time_list.append({'number': number, 'process': 'undefined',
                                               'start': start, "stop": when, 
                                               'how': how})
                    cur = cur.strip()
        else: # any version of topspin from 2.1 and up
            ##AUDIT TRAIL=  $$ (NUMBER, WHEN, WHO, WHERE, PROCESS, VERSION, WHAT)
            while len(cur) > 2:
                if cur.startswith('('):
                    cur = cur[1:]
                    number, cur = cur.split(",",1)
                    when, cur = cur.split(",",1)
                    when = when.strip("<>")
                    who, cur = cur.split(",",1)
                    who = who.strip("<>")
                    where, cur = cur.split(",",1)
                    where = where.strip("<>")
                    process, cur = cur.split(",",1)
                    process = process.strip("<>")
                    version, cur = cur.split(",",1)
                    version = version.strip("<>")
                    what, cur = cur.split(">)",1)
                    if 'go' in process:
                        when =  parser.parse(when)
                        what = what.strip("<>\n\r \t")
                        try:
                            created, start = what.split("started at ", 1)
                            start, _ = start.split(",", 1)
                        except: 
                            # if no started at line found then skip the record
                            # it is usually a "continuing with go" line
                            cur = cur.strip()
                            continue
                        try: 
                            start = parser.parse(start)
                        except: 
                            # cannot parse the start (empty string can happen)
                            # then use the end time...
                            # print "cannot parse start date in started at line" 
                            start = when
                        time_list.append({'number': number, 'process': process,
                                               'start': start, "stop": when, 
                                               'how': created, 'what': what})
                    cur = cur.strip()
        
    #    return time_list
    # time_list 
        if len(time_list) == 0 :
            return (0, 0, 0)
        total_exp_time = timedelta(0)
        start_time = None
        stop_time = None
        last_go = True
        for i in time_list[-1::-1]: # loop from last entry to first
            if 'continue with go' in i['how']:
                if last_go:
                    stop_time = i['stop']
                    last_go = False
                if start_time is None:
                    start_time = i['start']
                total_exp_time +=  i['stop']-i['start']
                continue
            if 'created by zg' in i['how']:
                if stop_time is None:
                    stop_time = i['stop']
                start_time = i['start']
                total_exp_time +=  i['stop']-i['start']
                break
        return start_time, stop_time, total_exp_time # time_list #(time_list[0]['start'], time_list[-1]['stop'], total_exptime)

