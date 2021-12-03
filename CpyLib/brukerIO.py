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


# Changes
# 27/02/2017 by JT
# fix calculation of tdblock according to DTYPA:
#                       need to manage NC depending on DTYPA
# 23/02/2017 by JT
# add management of DTYPA and DTYPP for topspin 4

# 26/08/2015 by JT
# add effective digital filter removal (applies 1st order correction
# with FFT, iFFT process)
# for readfidc and add readserc function
# new functions:
# serc2DEAE2HC, serc2DStatesTppi2HC, serc2DStates2HC to use complex arrays from
#                    readserc instead of readser
#
# change indentation from tab to 4 spaces
# change version number
# corrected bug when writing string (missing <>)
# 27/08/2014 by JT
# in readfid and readser calculate the number of dig filt to remove
# with int(round(self.getdigfilt())) instead of int(self.getdigfilt())

# 25/08/2014 by JT
# increment library version to 1.4
# add readfidc and writefidc function

# 24/07/2012:
# read and write of ser file can be done on nD datasets


# TODO: 3D or more dataset for read and write of processed data
#        improve processed data unit management
#        new function getprocunit
#        new function getprocx, getprocy automatically based on
#                                           unit (s ppm Hz or other...)

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
import numpy.core as np
import numpy.fft as fft

pyver = sys.version
# print("python version: " + pyver)

if pyver < "2.2":
    print("python version: " + pyver)
    raise Exception("current version %s. version >= 2.2 required!" % (pyver,))

# a workaround for pad function not available with numpy version < 1.7 : lets make it available within brukerIO library:
try:
    # for now I only use my pad version
    raise
    from numpy import pad
except:
    from numpy import concatenate
    def pad(array2pad, pad_shape, *args, **kwargs):
        """Pad the spectra in selected dimensions. Same as numpy pad. 

        This method act ss a fall back method when numpy too old and does not contain 
        the pad method

        --- Arguments ---
        array2pad : the array that is zero filled
        pad_shape : a tuple of (before, after) pad size
        --- Returns --- 
        the padded array

        example  :  a = np.array([[1,2] [3, 4]])
                    pad(a,((0,2), (1, 1)),'')
                    a == [[0, 1, 2, 0], [0, 3, 4, 0], [0, 0, 0, 0]]
        """
        pad_shape = np.asarray(pad_shape)
        if len(pad_shape.shape) == 1:
            pad_shape = pad_shape.reshape(1,len(pad_shape))
        for i in range(len(pad_shape)):
            shape = array2pad.shape
            before_shape = list(shape)
            after_shape = list(shape)
            before, after = pad_shape[i] 
            after_shape[i] = after
            before_shape[i] = before
            array2pad = concatenate((np.zeros(before_shape), array2pad, np.zeros(after_shape)), axis=i)
        return array2pad
#        return r1 = numpy.concatenate((numpy.zeros(int_before), array2pad,
#                                       numpy.zeros(int_after)))
            

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


def serc2DStates2HC(ser):
    """Transform a ser file read with readserc  of shape (TD1, Td2/2) of dataset acquired in States Mode
    into hypercomplex representation array of shape (2, TD1/2, TD2/2)
    arguments ---- 
    ser : a complex array with alternated States rows in dimension TD1
    returns ------
    a view with updated shape  (2, TD1/2, TD2)
    """
    (td1, td2) = ser.shape
    td1 = td1//2*2
    ser = ser[0:td1]
    tmp = ser.reshape(td1//2, 2, td2)
    tmp = tmp.swapaxes(1, 0)
    return tmp


def serc2DStatesTppi2HC(ser):
    """
     transform a ser file read with readserc of dataset acquired in States-TTPI
     Mode into hypercomplex representation array of shape (2xTD1/2xTD2)
    """
    (td1, td2) = ser.shape
    td1 = td1//2*2  # TD1 must be even
    ser = ser[0:td1]
    # separate reals and imaginaries
    tmp = ser.reshape(td1//2, 2, td2)
    tmp[1::2] *= -1  # multiply every other row by -1 to turn into States mode
    tmp = tmp.swapaxes(1, 0)
    return tmp


def serc2DEAE2HC(ser):
    """
   Transform a ser file read with readserc of dataset acquired in Echo-AntiEcho
   Mode into hypercomplex representation array of shape (2xTD1/2xTD2)
    """
    (td1, td2) = ser.shape
    td1 = td1//2*2
    ser = ser[0:td1]
    tmp = ser.reshape(td1//2, 2, td2)
    tmp = tmp.swapaxes(1, 0)
    R = np.concatenate((0.5*(tmp[0]+tmp[1]), 0.5*(tmp[0]-tmp[1])
                       )).reshape(2, td1//2, td2//2)
    return R


# obsolete functions:
def ser2DStates2HC(ser):
    """DEPRECATED: transform a just read ser file of 2D data acquired in
States Mode into hypercomplex representation array of shape (2xTD1/2xTD2/2) """
    (td1, td2) = ser.shape
    td1 = td1//2*2
    ser = ser[0:td1]
    tmp = ser.reshape(td1//2, 2, td2//2, 2)
    tmp = tmp[..., 0] + 1j*tmp[..., 1]
    tmp = tmp.swapaxes(1, 0)
    return tmp


def ser2DStatesTppi2HC(ser):
    """DEPRECATED: transform a just read ser file of 2D data acquired in
    States-TPPI Mode into hypercomplex representation array of shape
    (2, TD1/2, TD2/2)
    """
    (td1, td2) = ser.shape
    td1 = td1//2*2
    ser = ser[0:td1]
    # separate reals and imaginaries
    tmp = ser.reshape(td1//2, 2, td2//2, 2)
    tmp = tmp[..., 0] + 1j*tmp[..., 1]
    tmp[1::2] *= -1
    tmp = tmp.swapaxes(1, 0)
    return tmp


def ser2DEAE2HC(ser):
    """DEPRECATED: transform a just read ser file of 2D data acquired in
    Echo-AntiEcho mode into hypercomplex representation array of shape
    (2xTD1/2xTD2/2)
    """
    (td1, td2) = ser.shape
    td1 = td1//2*2
    ser = ser[0:td1]
    tmp = ser.reshape(td1//2, 2, td2//2, 2)
    tmp = tmp[..., 0] + 1j*tmp[..., 1]
    tmp = tmp.swapaxes(1, 0)
    R = np.concatenate((0.5*(tmp[0] + tmp[1]), 0.5*(tmp[0]-tmp[1])
                       )).reshape(2, td1//2, td2//2)
    return R


def rephase(self, NdArray, phase=0, dim=0):
    """
    Rephase the dim n of an hyper complex array of shape (dim0, dim1, ..,
    dim n, ...) where dim n has size 2 and contains the hypercomplex values.
    INPUT:     NdArray
        phase to apply in degree in that dimension
        dimension containing the Re/Im pairs
    OUTPUT: NdArray
    """
    cosP = np.cos(phase/360.0*2*np.pi)
    sinP = np.sin(phase/360.0*2*np.pi)
    NdArray.swapaxes(dim, -1)
    NdArray[..., 0], NdArray[..., 1] = (
            cosP*NdArray[..., 0] - sinP*NdArray[..., 1],
            cosP*NdArray[..., 1]+sinP*NdArray[..., 0])
    NdArray.swapaxes(dim, -1)
    return NdArray


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
    * =readfidc(rmGRPDLY=False(|True), applyNC=True(|False)
                                              returns cplx numpy.array
    * =writefidc(cplx array)                  returns nothing
    * =readfid(raw=False(|True))              returns numpy.array
    * =writefid(fid)                          returns nothing
    * =readser(raw=False(|True))              returns numpy.array
    * =writeser(serArray, raw=True(|False))    returns nothing
    * =readspect1d(name="1r"(|"1i"))          returns numpy.array
    * =readspect1dri()                        returns numpy.array, numpy.array
    * =writespect1dri(spectRe, spectIm)       returns nothing
    * =readspect2d(name="2rr"(|2ri|2ir|2ii))  returns numpy.array
    * =writespect2d(spectArray, name="2rr"(|2ri|2ir|2ii))
                                              returns nothing
    * =readspectnd(name="2rr"|2ri|2ir|3rrr....)
                                              returns numpy.array
    * =getxtime()                             returns numpy.array
    * =getytime()                             returns numpy.array
    * =getprocxhz()                           returns numpy.array
    * =getprocyhz()                           returns numpy.array
    * =getprocxppm()                          returns numpy.array
    * =getprocyppm()                          returns numpy.array
    * =getxhz()                               returns numpy.array
    * =getyhz()                               returns numpy.array
    * =getxppm()                              returns numpy.array
    * =getyppm()                              returns numpy.array
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

        self.dtypeA = np.dtype(brukBYTORD[brukBYTORDA] + brukDTYP[BrukDTYPA])
        # print("acq data stored as %s of size %d" % (self.dtypeA,
        #                                             self.dtypeA.itemsize))
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

        self.dtypeP = np.dtype(brukBYTORD[brukBYTORDP] + brukDTYP[BrukDTYPP])
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

    def delete_processed_data(self):
        import itertools
        import os
        # list of files '1r', '2ri', '3rir' for example
        files = [str(self.dimP) + ''.join(ri) for ri in itertools.product(['r', 'i'], repeat=self.dimP)]
        print("deleting" + ' '.join(files))
        for f in files: 
            try:
                os.remove(self.returnprocpath() + f)
            except FileNotFoundError:
                # all files may not exist, just skip silently
                pass
     
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

    def readfid(self, raw=False):
        """
        read an fid (1D) file and return it as numpy array
        The FID has the digital filter part removed and it's amplitude
                is scaled according to NC parameter (NC such that stored data lie in between 2^28 and 2^29)
        If raw is true it returns the unscaled FID including the digital
            filter part
        """
        filename = self.returnacqpath() + "fid"
        if not os.path.exists(filename):
            raise FileNotFoundError("Fid file %s not found." % (filename, ))
        scale = self.readacqpar("NC", True)
        td = self.readacqpar("TD", True)
        res = np.fromfile(filename, dtype=self.dtypeA, count=td).astype(float)
        npts = 2*int(round(self.getdigfilt()))
        if raw:
            return res
        else:
            return res[npts:]*2**scale

    def writefid(self, spect):
        """
        write an fid (1D) file and return nothing
        Do not deal with digital filter.
        """
        from math import ceil
        from math import log as ln
        filename = self.returnacqpath() + "fid"
        if self.dtypeA != np.dtype('float64'):
            # recalculate a good NC value
            MAX = np.abs(spect).max()
            if MAX > 0:
                NC = int(ceil(ln(MAX/2)/ln(2)))-29
            else:
                NC = 0
        else:
            NC = 0

        TD = len(spect)
        # filesize should be a multiple of a block of 1024 bytes
        # calculates the number of points per block
        ptpblk = 1024./self.dtypeA.itemsize
        # rounds TD to the next block size
        tdblock = int(ceil(TD/ptpblk)*ptpblk)
#        print(TD, tdblock, tdblock-TD)
        spect = spect/2**NC
        res = np.concatenate((spect, np.zeros(tdblock-len(spect))))

        self.writeacqpar("NC", NC, True)
        self.writeacqpar("TD", TD, True)
        res.astype(self.dtypeA).tofile(filename)

    def readfidc(self, rmGRPDLY=True, applyNC=True):
        """
        read a bruker fid (1D) file and return it as a single complex
            numpy array
        If rmGRPDLY=True then the first int(GRPDLY) complex points are
            removed from the beginning of the FID
        If applyNC=False then the array is not multiplied by 2**NC
        """
        filename = self.returnacqpath() + "fid"
        if not os.path.exists(filename):
            raise FileNotFoundError("Fid file %s not found." % (filename, ))
        td = self.readacqpar("TD", True)
        res = np.fromfile(filename, dtype=self.dtypeA, count=td).astype(float)
        res = res.reshape((td//2, 2))
        R = res[:, 0]+1j*res[:, 1]
        phcfilt = self.getdigfilt()
#        print("phcfilt", phcfilt)
        npts = int(phcfilt)
        if applyNC:
            scale = self.readacqpar("NC", True)
            R *= 2**scale
        if rmGRPDLY:
            # Steps to remove digfilt according to Bruker pprocessing:
            # Do FFT of FID (spectrum size must be even due to bug below)
            # Apply fftshift
            # Reverse array order (to present data with up frequency
            #                      pointing left)
            # Roll array by one point to the right (roll(FT, +1))
            # Apply a first order phase of exp(-2*1j*pi*phcfilt/fftsize*n)
            #       with n the index of spectrum point
            # Apply reverse processing: roll -1 then reverse order then
            #       ifftshift then ifft
            fftsize = td//2
            PH = np.exp(-1j*np.pi*2*phcfilt*np.arange(fftsize)/float(fftsize))
            FT = np.roll(fft.fftshift(fft.fft(R, fftsize))[::-1], 1)
            R = fft.ifft(fft.ifftshift(np.roll(FT*PH, -1)[::-1]))
            # discard the digital filter points at the end of FID
            R = R[0:td//2-npts]
        return R

    def writefidc(self, spect):
        """
        write an fid (1D) file and return nothing
        Do not deal with digital filter.
        """
        from math import ceil
        from math import log as ln
        filename = self.returnacqpath() + "fid"
        # recalculate a good NC value
        if self.dtypeA != np.dtype('float64'):
            MAX = np.absolute(spect).max()
            if MAX > 0:
                NC = int(ceil(ln(MAX/2)/ln(2)))-29
            else:
                NC = 0
        else:
            NC = 0

        TD = len(spect)*2
        # filesize should be a multiple of 1k block
        # calculates the number of points per block
        ptpblk = 1024.0/self.dtypeA.itemsize
        # rounds TD to the next block size
        tdblock = int(ceil(TD/ptpblk)*ptpblk)
#        print(TD, tdblock, tdblock-TD)
        spect = spect/2**NC
        S = np.zeros(tdblock)
        S[0:TD:2] = spect.real
        S[1:TD:2] = spect.imag
#        print(NC)
        self.writeacqpar("NC", NC, True)
        self.writeacqpar("TD", TD, True)
        S.astype(self.dtypeA).tofile(filename)

    def readser(self, raw=False):
        """
        read a ser (2D and 3D only) file and return it as numpy 2D array
        removes digital filter and trailing data unless raw is True
        """
        from math import ceil
        filename = self.returnacqpath() + "ser"
        if not os.path.exists(filename):
            raise FileNotFoundError("Ser file %s not found." % (filename, ))
        # PARMODE contains 0 for 1D, 1 for 2D, 2 for 3D, n-1 for nD
        dim = self.readacqpar("PARMODE", True) + 1
        # ordre de stockage des dim 2 et 3
        # aqseq=0 acqus puis acqu2s puis acqu3s
        # aqseq=1 acqus puis acqu3s puis acqu2s
        # aqseq initialised to -1 when not used

        aqseq = -1
        if dim > 2:
            aqseq = self.readacqpar("AQSEQ", True)
        scale = self.readacqpar("NC", True)
        TD = self.readacqpar("TD", True)
        tdnd = []
        tdn = 1
        for i in range(2, dim+1):
            tmptd = self.readacqpar("TD", True, dimension=i)
            tdnd.insert(0, tmptd)
            tdn *= tmptd
        if aqseq == 1:
            (tdnd[-2], tdnd[-1]) = (tdnd[-1], tdnd[-2])
        # ser file contains FID of blocks of 256 points
        # thus one needs to calculate the length of 1 FID
        # calculates the number of points per block
        ptpblk = 1024.0/self.dtypeA.itemsize
        # rounds TD to the next block size
        tdblock = int(ceil(TD/ptpblk)*ptpblk)

        tdnd.append(tdblock)
        res = np.fromfile(filename, dtype=self.dtypeA,
                         count=tdn*tdblock).astype(float)
        res.resize(tdnd)
        # get digital filter length
        npts = 2*int(round(self.getdigfilt()))
        # rescaling values according to NC_acqu and
        # removing digital filter if asked
        if raw:
            return res
        else:
            return res[..., npts:TD]*2**scale

    def readserc(self, rmGRPDLY=True, applyNC=True):
        """
        Read a ser file and return it as numpy nD complex array
        If rmGRPDLY=True then the digital filter is removed from the
            beginning of the FIDs
        If applyNC=True then the array is multiplied by 2**NC
        """
        from math import ceil

        # get the location of ser file and check for existence
        filename = self.returnacqpath() + "ser"
        if not os.path.exists(filename):
            raise FileNotFoundError("Ser file %s not found." % (filename, ))
        # determine rank
        # PARMODE contains 0 for 1D, 1 for 2D, 2 for 3D, n-1 for nD
        dim = self.readacqpar("PARMODE", True) + 1
        # determine dimension ordering for dim 2 and 3 in 3D datasets
        # aqseq=0 acqus then acqu2s then acqu3s
        # aqseq=1 acqus then acqu3s then acqu2s
        # aqseq initialised to -1 when not used
        aqseq = -1
        if dim > 2: # if 3D or more dataset
            aqseq = self.readacqpar("AQSEQ", True)
        # AQSEQ 3D: {'0': '321', '1', '312'}
        # AQSEQ 4D: {'0': '4321', '1', '4312', ...?}
        # tdnd list size of dims based on status TD
        tdnd = []
        # tdn full size of array except first dim
        tdn = 1
        for i in range(2, dim+1):
            tmptd = self.readacqpar("TD", True, dimension=i)
            tdnd.insert(0, tmptd)
            tdn *= tmptd
        if aqseq == 1:
            (tdnd[-2], tdnd[-1]) = (tdnd[-1], tdnd[-2])

        # ser file contains FID of blocks of 256 points (1024 bytes, 256xint32)
        # thus one needs to calculate the length of 1 FID
        # make sure of the 256 block boundary for direct dimension
        TD = self.readacqpar("TD", status=True, dimension=1)
        # calculates the number of points per block
        ptpblk = 1024.0/self.dtypeA.itemsize
        # rounds TD to the next block size
        tdblock = int(ceil(TD/ptpblk)*ptpblk)
        tdnd.append(tdblock//2)
        tdnd.append(2)

        # read file
        res = np.fromfile(filename, dtype=self.dtypeA,
                         count=tdn*tdblock).astype(float)
        # reshape or resize ? there should be no reason to change overal
        # size if tdn*tdblock are read but returning a view or copy may matter.
        res = res.reshape(tdnd)
        R = res[..., 0:TD, 0] + 1j * res[..., 0:TD, 1]

        # rescaling values according to NC_acqu and
        # removing digital filter if asked
        if applyNC:
            scale = self.readacqpar("NC", True)
            R *= 2**scale
        if rmGRPDLY:
            # Steps to remove digfilt according to Bruker pprocessing:
            # Do FFT of FID (spectrum size must be even due to bug below)
            # Apply fftshift
            # Reverse array order (to present data with up frequency
            #         pointing left)
            # Roll array by one point to the right (roll(FT, +1))
            # Apply a first order phase of exp(-2*1j*pi*phcfilt/fftsize*n)
            #       with n the index of spectrum point
            # Apply reverse processing: roll -1 then reverse order then
            #       ifftshift then ifft
            phcfilt = self.getdigfilt()
            npts = int(phcfilt)
            fftsize = TD//2
            PH = np.exp(-1j*np.pi*2*phcfilt*np.arange(fftsize)/float(fftsize))
            FT = np.roll(fft.fftshift(fft.fft(R, fftsize),
                                     axes=-1)[..., ::-1], 1, axis=-1)
            R = fft.ifft(fft.ifftshift(np.roll(FT*PH, -1,
                                       axis=-1)[..., ::-1], axes=-1))
            # discard the digital filter points at the end of FID
            R = R[..., 0:TD//2-npts]
        return R

    def writeser(self, serArray, raw=True):
        """
        Write a nD array into a ser file
        Everything should be done on raw data (readser(raw=true))
        Digital filter info from original dataset is not altered
        It is the user responibility to change DIGMOD or GRPDLY according
           to the writen ser file
        Raw flag is not evaluated
        Remark: 3D and more are treated as 2D and one should store manually
                the different sizes td1 to td3
        """

        from math import ceil
        from math import log as ln

        filename = self.returnacqpath() + "ser"
        if not os.path.exists(filename):
            raise FileNotFoundError("Ser file %s not found." % (filename, ))

        arrayShape = serArray.shape
        # dim =0 pour 1D, 1 pour 2D etc...
        dim = self.readacqpar("PARMODE", True) + 1
        # ordre de stockage des dimensions 2 et 3 pour les 3D
        # aqseq=0 acqus puis acqu2s puis acqu3s
        # aqseq=1 acqus puis acqu3s puis acqu2s
        # aqseq initialised to -1 when not used
        """
        AQSEQ contains an integer that codes the dimension (F1, F2, F3 as
              they appear in eda and refering to acqus, acqu2s, acqu3s
              etc...) storage order.
        For 2D there is no need for it. the value is always 0
        For 3D one has the following order:
            0: F3F2F1
            1: F3F1F2
        For 4D only natural order is allowed : 
            0: F4F3F2F1
        If AQSEQ is not set (-1 ???) then AQORDER is used
        """
        aqseq = -1
        if dim > 2:
            aqseq = self.readacqpar("AQSEQ", True)

        if len(arrayShape) != dim:
            raise TypeError("dataset is %sD while array is %sD: giving up" % (
                  str(dim), str(len(arrayShape))))

        TD = arrayShape[-1]

        # filesize should be a multiple of a block of 1024 bytes
        # calculates the number of points per block
        ptpblk = 1024.0/self.dtypeA.itemsize
        # rounds TD to the next block size
        tdblock = int(ceil(TD/ptpblk)*ptpblk)
        if tdblock != TD:
            newShape = list(arrayShape)
            newShape[-1] = tdblock-TD
            serArray = np.concatenate((serArray, np.zeros(newShape)),
                                      axis=len(newShape)-1)

        # scale = self.readacqpar("NC", True)

# calculates NC_proc to use maximum dynamics on signed 32 bits int
# actually NC such that max lies between 2^28 and 2^29 (to avoid overflow when rephasing)
# cf. Bruker processing reference
        sizeA = serArray.size

        # NC enlever 17 soit presque la moitie de 31 ????
        if self.dtypeA != np.dtype('float64'):
            MAX = np.max(np.fabs(serArray.reshape(sizeA)))
            if MAX > 0:
                NC = int(ceil(ln(MAX)/ln(2)))-29
            else:
                NC = 0
            serArray /= 2**NC
        else:
            NC = 0

        self.writeacqpar("NC", NC, True)
        serArray.astype(self.dtypeA).tofile(filename)
        self.writeacqpar("TD", TD, True, 1)

        if aqseq == 1:
            (arrayShape[-3], arrayShape[-2]) = (arrayShape[-2],
                                                arrayShape[-3])
        for i, td in enumerate(arrayShape[::-1]):
            self.writeacqpar("TD", td, True, dimension=i+1)
        return

    def readspect1d(self, name="1r"):
        """
        reads a 1D processed bruker file
        file name is either 1r (default) or 1i
        returns a numpy array or None if file is not found
        """
        filename = self.returnprocpath() + name
        if not os.path.exists(filename):
            raise FileNotFoundError("Spectrum file %s not found." % (name, ))
        scale = self.readprocpar("NC_proc", True)
        si = self.readprocpar("SI", True)
        res = np.fromfile(filename, dtype=self.dtypeP, count=si).astype(float)
        return res*2**scale

    def readspect1dri(self):
        """
        reads a 1D complex processed bruker data
        files 1r and 1i
        returns a tuple of 2 numpy arrays or None if file is not found
        """
        return self.readspect1d("1r"), self.readspect1d("1i")

    def writespect1dri(self, spect1, spect2):
        """
        Write a 1D processed datafile
        Files writen are 1r 1i
        """
        s1=spect1.copy()  # make copy in case spect1 and 2 refer to same object
        s2=spect2.copy()
        from math import log as ln
        from math import ceil
        f1 = self.returnprocpath() + "1r"
        f2 = self.returnprocpath() + "1i"
        # calculates NC_proc to use maximum dynamics on signed 32 bits int
        MAX = np.max(np.absolute(s1+1j*s2))
        if self.dtypeP != np.dtype('float64'):
            # recalculate a good NC value
            if MAX > 0:
                NC = int(ceil(ln(MAX)/ln(2)))-29
            else:
                NC = 0
        else:
            NC = 0
#        print("NC=%d max=%f" % (NC, MAX))
        (si, ) = s1.shape
#        print(s1)
#        print(2**NC)
#        print(s1/(2**NC))
        s1 *= 1./(2**NC)
        s2 *= 1./(2**NC)

#        print(s1)
        s1.astype(self.dtypeP).tofile(f1)
        s2.astype(self.dtypeP).tofile(f2)
        # write some parameters related to spect arrays used by topspin
        self.writeprocpar("NC_proc", NC, True)
        # not sure whether to change si and of not
        self.writeprocpar("STSI", si, True)
        self.writeprocpar("SI", si, True)
        self.writeprocpar("SI", si, False)
        # topspin uses this parameter to scale display to full amplitude:
        # note it is using the int value not the absolute (int*2^NC_proc)
        # this may not be true for topspin 3.0...
        maxSpect = s1.max()
        minSpect = s1.min()
        self.writeprocpar("YMAX_p", maxSpect, True)
        self.writeprocpar("YMIN_p", minSpect, True)
        return

    def xdim_unfold(self, spect):
        """ Unfold the XDIM storing order to regular array 
            spect shape is supposed to reflect SI,
            XDIM parameters are read from proc_s
        """
        
        SI = spect.shape
        rank = len(spect.shape)
        XDIMs = []
        RESTs = []
        for i, si_i in enumerate(si):
            XDIMs.insert(0, self.readprocpar("XDIM", status=True, dimension=rank-i))
            RESTs.insert(0, si[i]//xdim[0])
        spect = spect.reshape(RESTs + XDIMs)
        for i in range(rank-1):
            spect = np.rollaxis(spect, rank+i, 1+2*i)
        return spect.reshape(SI)

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
                MC2 = States[-TPPI](t2) / States[-TPPI](t1) : hypercomplex acquisition in both dimensions
                    FT(t1, t2, t3)
                    FT(no, no,no) ->  3rrr, 3irr (to be confirmed)
                    FT(no, no,fqc) ->  3rrr, 3irr
                    FT(no, fsc, fqc) -> 3rrr, 3rir
                    FT(fsc, no, fqc) -> 3rrr, 3rri
                    FT(fsc, fsc, fqc) -> 3rrr, 3rri or 3rir depending if tf2 or tf1 was first
                    after 3D FT, Hilbert Transform (HT) in F3 adds 3irr, in F2 adds 3rir but there are still some missing octants like 3iii, 3iir, 3iri, 3rii.
                    A priori, no inverse transform is feasible
                MC2 = QF(t2) / States(t1)
                    FT(t1, t2, t3)
                    FT(no, no, no) -> 3rrr, 3iii (to be confirmed) 
                    FT(no, no, fqc) -> 3rrr, 3iii
                    FT(no, fqc, fqc) -> 3rrr, 3iii
                    FT(fqc, no, fqc) -> 3rrr, 3iii, 3rri
                    FT(fqc, fqc, fqc) -> 3rrr, 3rri (tf3;tf2;tf1) or 3iii (tf3;tf1;tf2)
                MC2 = States(t2) / QF(t1)
                    FT(t1, t2, t3)
                    FT(no, no, no) -> 3rrr, 3iii (to be confirmed) 
                    FT(no, no, fqc) -> 3rrr, 3iii
                    FT(no, fqc, fqc) -> 3rrr, 3rir, 3iii
                    FT(fqc, no, fqc) -> 3rrr, 3iii
                    FT(fqc, fqc, fqc) -> 3rrr, 3iii (tf3;tf2;tf1) or 3rir (tf3;tf1;tf2), 
                MC2 = QF(t2) / QF(t1)
                    FT(t1, t2, t3)
                    FT(no, no, no) -> 3rrr, 3iii (to be confirmed) 
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

    def xdim_fold(self, spect, XDIMs):
        """ Fold spect ndArray according to XDIM storing order 
            spect shape is supposed to reflect SI,
            XDIMs is an array of same rank as spect 
        """
        SIs = spect.shape
        rank_spect = len(SIs)
        rank_XDIMs = len(XDIMs)
        if rank_spect != rank_XDIMs:
            raise ValueError("spect (%dD) and XDIMs (%dD) do not have same rank." % (rank_spect, rank_XDIMs))
#        for i in range(DIM):
#            XDIMs.insert(0, self.readprocpar("XDIM", True, i+1))
        RESTs = [i//j for i, j in zip(SIs, XDIMs)]
        import itertools
        spect = spect.reshape(list(itertools.chain(*zip(RESTs, XDIMs))))
        for i in range(rank_spect-1):
            spect = np.rollaxis(spect, 2*(i+1), 1+i)
        return spect

    def readspect2d(self, name="2rr"):
        """
        Read a 2D processed datafile
        File is 2rr (default), 2ri, 2ir or 2ii
        Returns a 2D numpy array or None if file is not found
        Does not account for STSR, STSI!!!
        """
        filename = self.returnprocpath() + name
        if not os.path.exists(filename):
            raise FileNotFoundError("Spectrum file %s not found." % (filename, ))
        scale = self.readprocpar("NC_proc", True)
        SIs = np.array([self.readprocpar("SI", status=True, dimension=dim) for dim in [2, 1]])
        XDIMs = np.array([self.readprocpar("XDIM", status=True, dimension=dim) for dim in [2, 1]])
        RESTs = SIs//XDIMs
        spect = np.fromfile(filename, dtype=self.dtypeP,
                           count=SIs.prod()).astype(float)
        spect = spect*2**scale
        spect = spect.reshape(np.concatenate((RESTs, XDIMs)))
        spect = spect.swapaxes(1, 2)
        spect = spect.reshape(SIs)
        return spect

    def writespect2dall(self, spect_array_list, MC2=None, dType=None):
        """
        write a spectrum to 2D processed datafiles (2rr, 2ri etc..)
        written files are chosen according to FnMode/MC2 parameters 
        dType is data type in F2/F1: "XY" with X or Y being "t" for time, "f"
            for frequency "e" for experiment (no unit)
        Examples: dType="ff", dType="ft", dType="fe"
        """
        from math import ceil
        from math import log as ln
        dir_proc_path = self.returnprocpath()
        if MC2 is None:
            MC2 = self.readprocpar("MC2", dimension=2, status=False)
        """
        # managing dType  "f2/f1" "tt", "ft", "ff", "te", "fe", "tf"
        t means time domain : if F1 is in time domain we consider hypercomplex is not treated yet (ft_mode(F1) not is ift)
        f means frequency domain
        # managing MC2 (see self.MC2_list for valid values)
        QF (tt, ft, ff : 2rr 2ii)
        not QF (tt, ft: 2rr 2ir, ff: + 2ri + 2ii)
        """
        QF_names = ["2rr", "2ii"]
        other = ["2rr", "2ir"]
        if dType[1] == 'f': 
            if   dType[0] == 't':
                """ dType='tf' is not implemented yet"""
                raise ValueError("dType='tf' is not implemented yet")
            elif dType[0] == 'f':
                if MC2 == 0: #QF
                    names = ['2rr', '2ii']
                else :
                    names = ['2rr', '2ir', '2ri', '2ii']
        elif dType[1] == 't':
            if MC2 == 0: # QF
                names = ['2rr', '2ii']
            else :
                names = ['2rr', '2ir']
        elif dType[1] == 'e':
            """e requires QF, or QF(no-frequency) : MC2 is not checked"""
            names = ['2rr', '2ii']
        
        MAXar = np.absolute(np.ravel(spect_array_list[0]) + 1j*np.ravel(spect_array_list[1]))
        MAX = np.max(MAXar)
        if len(names) == 4:
            MAXai = np.absolute(np.ravel(spect_array_list[2]) + 1j*np.ravel(spect_array_list[3] ))
            MAX = np.max(np.absolute(MAXar) + 1j*np.absolute(MAXai))

        # xdim is not optimized... I use :
        SIs = list(spect_array_list[0].shape)
        XDIMs = SIs[:]

        if self.dtypeP != np.dtype('float64'):
            # recalculate a good NC value
            if MAX > 0:
                NC = int(ceil(ln(MAX)/ln(2)))-29
            else:
                NC = 0
        else:
            NC = 0
        smin = int(spect_array_list[0].ravel().min()/2**NC)
        smax = int(spect_array_list[0].ravel().max()/2**NC)
        if smax > 2**31 or smin < -2**31:
            raise ValueError("Stored int32 spectrum exceeds 2**31 magnitude. Wrong NC ? How could this happen ?")
        for dim in [1, 2]:
            self.writeprocpar("NC_proc", NC, status=True, dimension=dim)
            self.writeprocpar("XDIM", XDIMs[-dim], status=True, dimension=dim)
            self.writeprocpar("STSI", SIs[-dim], status=True, dimension=dim)
            self.writeprocpar("SI", SIs[-dim], status=True, dimension=dim)
            # topspin YMAX/YMIN to scale display to full amplitude:
            # note it is using the int value not the absolute (int*2^NC_proc)
            self.writeprocpar("YMAX_p", smax, status=True, dimension=dim)
            self.writeprocpar("YMIN_p", smin, status=True, dimension=dim)

        self.writeprocpar("MC2", MC2, True, 2)
        if dType[0] == 'f':  # assume fqc FT applied in direct dimension
            self.writeprocpar("FT_mod", 6, True, 1)
            self.writeprocpar("FTSIZE", SIs[-1], True, 1)
        if dType[1] == 'f':  
            self.writeprocpar("FTSIZE", SIs[-2], True, 2)
            if MC2 == 0 | MC2 == 3 | MC2 == 5:
                # fqc(6) used after xfb with MC2=0 QF
                # fqc(6) used after xfb with MC2=3 States
                # fqc(6) used after xfb with MC2=5 echo-antiecho
                self.writeprocpar("FT_mod", 6, True, 2)
            elif MC2 == 4:
                # fsc(4) used after xfb with MC2=4 States-TPPI
                self.writeprocpar("FT_mod", 4, True, 2)
            elif MC2 == 2:
                # fsc(5) used after xfb with MC2=2 TPPI
                self.writeprocpar("FT_mod", 5, True, 2)
        if dType[0] == 't':
            self.writeprocpar("FT_mod", 0, True, 1)
            self.writeprocpar("FTSIZE", 0, True, 1)
            self.writeprocpar("PKNL", False, True, 1) # at some point one needs to deal with PKNL... how ?
            self.writeprocpar("AXUNIT", "s", True, 1)
            # even though we are in time domain we need to set a SW_p in ppm
            # with respect to irradiation frequency SFO1
            # otherwise the OFFSET is not properly calculated in further 
            # topspin calculations especially in indirect dimension...
            sw2 = self.readacqpar("SW_h", status=True, dimension=1)
            dw2 = 1/sw2
            sfo2 = self.readacqpar("SFO1", status=True, dimension=1)
            self.writeprocpar("SW_p", (sw2/sfo2), status=True, dimension=1)
            self.writeprocpar("AXRIGHT", (SIs[-1]*dw2), status=True, dimension=1)
            self.writeprocpar("AXLEFT", 0.0, status=True, dimension=1)
        if dType[1] == 't':
            self.writeprocpar("FT_mod", 0, True, 2)
            self.writeprocpar("FTSIZE", 0, True, 2)
            self.writeprocpar("AXUNIT", "s", True, 2)
            # even though we are in time domain we need to set a SW_p in ppm
            # with respect to irradiation frequency SFO1
            # otherwise the OFFSET is not properly calculated in further 
            # topspin calculations especially in indirect dimension...
            sw1 = self.readacqpar("SW_h", status=True, dimension=2)
            dw1 = 1/sw1
            sfo1 = self.readacqpar("SFO1", status=True, dimension=2)
            self.writeprocpar("SW_p", (sw1/sfo1), status=True, dimension=2)
            # f_time:
            # a factor to calculate the AXRIGHT in time domain
            # if FnMODE=QF f_time = 1, else f_time = 2
            # This is bizarely related to sw_p calculated further by xf1
            # here one should account for FnMode but...
            f_time = 2 
            self.writeprocpar("AXRIGHT", (SIs[-2]*dw1/f_time), 
                              status=True, dimension=2)
            self.writeprocpar("AXLEFT", 0.0, status=True, dimension=1)
        RESTs = [si// xdim for si, xdim in zip(SIs,XDIMs)]
        for i, name in enumerate(names):
            filename = self.returnprocpath() + name
            spect = spect_array_list[i] / 2**(NC)
            spect = spect.reshape(RESTs + XDIMs)
            spect = spect.swapaxes(1, 2)
            spect.astype(self.dtypeP).tofile(filename)
            
    def writespect2d(self, spectArray, name="2rr", dType=None, MAX=None):
        """
        write a 2D processed datafile
        file is 2rr (default), 2ri, 2ir or 2ii
        dType is data type in F2/F1: "XY" with X or Y being "t" for time, "f"
            for frequency "e" for experiment (no unit)
        Examples: dType="ff", dType="ft", dType="fe"
        TODO: check for xdim calculation (now uses xdim=si)
              I REALLY should write 2 or 4 files depending on quadrature used: 2rr and 2ii or 2rr, 2ir, 2ri and 2ii
              There is also a the mode ift which is time but with hypercomplex t1 processed.
        """
        from math import ceil
        from math import log as ln
        filename = self.returnprocpath() + name
        SIs = spectArray.shape
        XDIMs = list(SIs)

        if name == '2rr':
            # calculates NC_proc to use maximum dynamics on signed 32 bits int
            sizeA = spectArray.size
            if MAX is None:
                MAX = np.max(np.fabs(spectArray.reshape(sizeA)))
#            print(MAX)
#            NC should be calculated on magnitude spectrum (2rr, 2ri, 2ir or 2ii)
#            not only on 2rr..
            if self.dtypeP != np.dtype('float64'):
                # recalculate a good NC value
                if MAX > 0:
                    NC = int(ceil(ln(MAX)/ln(2)))-29
                else:
                    NC = 0
            else:
                NC = 0
            # topspin uses this parameter to scale display to full amplitude:
            # note it is using the int value not the absolute (int*2^NC_proc)
            smax = int(MAX/2**NC)
            smin = -smax
            if smax > 2**31 or smin < -2**31:
                raise ValueError("Stored int32 spectrum exceeds 2**31 magnitude. Wrong NC ? How could this happen ?")
            for dim in [1, 2]:
                self.writeprocpar("NC_proc", NC, status=True, dimension=dim)
                self.writeprocpar("XDIM", XDIMs[-dim], status=True, dimension=dim)
                self.writeprocpar("STSI", SIs[-dim], status=True, dimension=dim)
                self.writeprocpar("SI", SIs[-dim], status=True, dimension=dim)
                self.writeprocpar("YMAX_p", smax, status=True, dimension=dim)
                self.writeprocpar("YMIN_p", smin, status=True, dimension=dim)
        else:
            NC = self.readprocpar("NC_proc", True)

    
        RESTs = [si // xdim for si, xdim in zip(SIs,XDIMs)]
        spectArray /= 2**(NC)
        spectArray = spectArray.reshape(RESTs + XDIMs)
        spectArray = spectArray.swapaxes(1, 2)
        spectArray.astype(self.dtypeP).tofile(filename)
#        print('OK')
        if dType:
            if dType[0] == 'f':  # assume fqc FT applied
                self.writeprocpar("FT_mod", 6, True, 1)
                self.writeprocpar("FTSIZE", SIs[-1], True, 1)
            if dType[1] == 'f':  # assume fqc FT applied
                # fqc(6) used after xfb with MC2=0 QF
                # fsc(5) used after xfb with MC2=2 TPPI
                # fqc(6) used after xfb with MC2=3 States
                # fsc(4) used after xfb with MC2=4 States-TPPI
                # fqc(6) used after xfb with MC2=5 echo-antiecho
                self.writeprocpar("FT_mod", 6, True, 2)
                self.writeprocpar("FTSIZE", SIs[-2], True, 2)
            if dType[0] == 't':
                self.writeprocpar("FT_mod", 0, True, 1)
                self.writeprocpar("FTSIZE", 0, True, 1)
                self.writeprocpar("AXUNIT", "s", True, 1)
                # even though we are in time domain we need to set a SW_p in ppm
                # with respect to irradiation frequency SFO1
                # otherwise the OFFSET is not properly calculated in further 
                # topspin calculations especially in indirect dimension...
                sw2 = self.readacqpar("SW_h", status=True, dimension=1)
                dw2 = 1/sw2
                sfo2 = self.readacqpar("SFO1", status=True, dimension=1)
                self.writeprocpar("SW_p", (sw2/sfo2), status=True, dimension=1)
                self.writeprocpar("AXRIGHT", (SIs[-1]*dw2), status=True)
            if dType[1] == 't':
                self.writeprocpar("FT_mod", 0, True, 2)
                self.writeprocpar("FTSIZE", 0, True, 2)
                self.writeprocpar("AXUNIT", "s", True, 2)
                # even though we are in time domain we need to set a SW_p in ppm
                # with respect to irradiation frequency SFO1
                # otherwise the OFFSET is not properly calculated in further 
                # topspin calculations especially in indirect dimension...
                sw1 = self.readacqpar("SW_h", status=True, dimension=2)
                dw1 = 1/sw1
                sfo1 = self.readacqpar("SFO1", status=True, dimension=2)
                self.writeprocpar("SW_p", (sw1/sfo1), status=True, dimension=2)
                self.writeprocpar("AXRIGHT", (SIs[-2]*dw1/2.0), status=True, dimension=2)
                
            # print(dType[0])
        return True

    def writespectnd(self, spectArray, name=None):
        """
        Write a nD processed datafile
        name is file name where to store data: 2rr, 2ri, 2ii, 3rrr, 4iiii etc...
        default to None, in which case automatic name is generated to X(r)X where X is rank and (r)X repeats r X times
        """
        from math import ceil
        from math import log as ln
        SIs = spectArray.shape

#        SIinit = spectArray.shape
#        SI = [SInext(si_i) for si_i in SIinit]
        spect_rank = len(SIs)

        # first check that processing rank matches spectArray rank
        
        proc_dim = self.readprocpar("PPARMOD", status=True, dimension=1)+1
        if proc_dim != spect_rank:
            raise ValueError("processing rank %dD does not match spectrum rank %dD." % (proc_dim, spect_rank))

        MAX = np.abs(spectArray).max()
        if self.dtypeP != np.dtype('float64'):
            # recalculate a good NC value
            if MAX > 0:
                if MAX > 0:
                    NC = int(ceil(ln(MAX)/ln(2)))-29
                else:
                    NC = 0
            else:
                NC=0
        else:
            NC = 0
        #NC = self.readprocpar("NC_proc", True)
        spectArray /= 2**(NC)
        XDIMs = list(SIs)                 # set XDIMs to SIs (no shuffling)
        spectArray = self.xdim_fold(spectArray, XDIMs)
        if name is None:
            name = str(spect_rank)
            for i in range(spect_rank):
                name += 'r'
        filename = self.returnprocpath() + name
        spectArray.astype(self.dtypeP).tofile(filename)
        self.writeprocpar("NC_proc", (NC), True, dimension=1)

        # topspin YMAX/YMIN to scale display to full amplitude:
        # note it is using the int value not the absolute (int*2^NC_proc)
        smin = int(spectArray.ravel().min())
        smax = int(spectArray.ravel().max())
        if smax > 2**31 or smin < -2**31:
            #print("whoowww Pb max=" + smax)
            raise ValueError("Stored int32 spectrum exceeds 2**31 magnitude. Wrong NC ? How could this happen ?")


        # assume only time domain for now without any processing (FT_mod='no')
        # set all optionnal processing parameters to 0
        ProcOptions = {"WDW"   : [["LB", 0], ["GB", 0], ["SSB", 0], ["TM1", 0], ["TM2", 0]],
                       "PH_mod": [["PHC0", 0], ["PHC1", 0]], "BC_mod": [["BCFW", 0], ["COROFFS", 0]],
                       "ME_mod": [["NCOEF", 0], ["LPBIN", 0], ["TDoff", 0]], 
                       "FT_mod": [["FTSIZE", 0], ["FCOR", 0], ["STSR", 0], ["STSI", 0], ["REVERSE", False]],
                      }
        for dim in range(1,spect_rank+1):
            self.writeprocpar("YMAX_p", (smax), status=True, dimension=dim)
            self.writeprocpar("YMIN_p", (smin), status=True, dimension=dim)
            for par in ProcOptions:
                self.writeprocpar(par, 0, status=True, dimension=dim)
                for opt in ProcOptions[par]:
                    self.writeprocpar(opt[0], opt[1], status=True, dimension=dim)

        # adjust required parameters : XDIM, SI, STSI
        for dim in range(1,spect_rank+1):
            self.writeprocpar("XDIM", XDIMs[-dim], status=True, dimension=dim)
            self.writeprocpar("SI", SIs[-dim], status=True, dimension=dim)
            self.writeprocpar("STSI", SIs[-dim], status=True, dimension=dim)
            # for further processing in topspin status SI and non status SI should match
#            self.writeprocpar("SI", SIs[-dim], status=False, dimension=dim)
 
    def readspectnd(self, name="2rr"):
        """
        Read a nD processed datafile
        File is 2rr (default), 2ri, 2ir, 2ii 3rrr etc....
        Returns a nD numpy array or None if file is not found
        Does not account for STSR
        """
        filename = self.returnprocpath() + name
        if not os.path.exists(filename):
            raise FileNotFoundError("Spectrum file %s not found." % (name, ))
        scale = self.readprocpar("NC_proc", True)
        num_dim = self.readprocpar("PPARMOD", True)+1
        SIs = []
        XDIMs = []
        RESTs = []
        size = 1
        for dim in range(1, num_dim+1):
            SIs.insert(0, self.readprocpar("STSI", True, dim))
            size *= si[0]
            XDIMs.insert(0, self.readprocpar("XDIM", True, dim))
            RESTs.insert(0, SIs[0]//XDIMs[0])
        spect = np.fromfile(filename, dtype=self.dtypeP,
                           count=size).astype(float)
        spect = spect*2**scale
        spect = spect.reshape(RESTs + XDIMs)
        for i in range(num_dim-1):
            spect = np.rollaxis(spect, num_dim+i, 1+2*i)
        spect = spect.reshape(si)
        return spect

    def getxtime(self):
        """
        Returns a numpy array containing the direct dimension ruler in s
        """
        dw = 1/self.readacqpar("SW_h", True)
        td = self.readacqpar("TD", True)
        return np.arange(0, td)*dw/2.

    def getytime(self):
        """
        Returns a numpy array containing the indirect dimension ruler in s
        Ruler follows rules from FnMODE:
        If TPPI States States-TPPI or echo/antiecho then it accounts for
           interleaved hyper complex rows
        """
        FnMode = self.readacqpar("FnMODE", True, 1)
        # FnMODE = 0 undefined
        #          1 QF
        #          2 QSEQ
        #          3 TPPI
        #          4 States
        #          5 States-TPPI
        #          6 echo/antiecho
        if (FnMode == 3 | FnMode == 4 | FnMode == 5 | FnMode == 6):
            f = 2.
        else:
            f = 1.0
        dw = 1/self.readacqpar("SW_h", True, 2)
        td = self.readacqpar("TD", True, 2)
        d0 = self.readacqpar("D 0", True, 1)
        return np.arange(0, td)*dw/f+d0

    def getprocxppm(self):
        """
        Returns a numpy array containing the direct dimension ruler in ppm
        """
        sw = self.readprocpar("SW_p", True)
        stsi = self.readprocpar("STSI", True)
        sf = self.readprocpar("SF", True)
        swp = sw/sf
        offset = self.readprocpar("OFFSET", True)
        ppmppt = swp/stsi
        ppm = -(np.arange(stsi)+0.5)*ppmppt+offset
        return ppm

    def getprocxhz(self):
        """
        Returns a numpy array containing the direct dimension ruler in ppm
        """
        sw = self.readprocpar("SW_p", True)
        stsi = self.readprocpar("STSI", True)
        sf = self.readprocpar("SF", True)
        swp = sw/sf
        offset = self.readprocpar("OFFSET", True)
        ppmppt = swp/stsi
        ppm = (-(np.arange(stsi)+0.5)*ppmppt+offset)*sf
        return ppm

    def getprocyppm(self):
        """
        Returns a numpy array containing the direct dimension ruler in ppm
        """
        sw = self.readprocpar("SW_p", True, 2)
        stsi = self.readprocpar("STSI", True, 2)
        sf = self.readprocpar("SF", True, 2)
        swp = sw/sf
        offset = self.readprocpar("OFFSET", True, 2)
        ppmppt = swp/stsi
        ppm = -(np.arange(stsi)+0.5)*ppmppt+offset
        return ppm

    def getprocyhz(self):
        """
        Returns a numpy array containing the direct dimension ruler in ppm
        """
        sw = self.readprocpar("SW_p", True, 2)
        stsi = self.readprocpar("STSI", True, 2)
        sf = self.readprocpar("SF", True, 2)
        swp = sw/sf
        offset = self.readprocpar("OFFSET", True, 2)
        ppmppt = swp/stsi
        return (-(np.arange(stsi)+0.5)*ppmppt+offset)*sf
        

# the following procedures recalculate the scales from acquisition parameters
    def getxhz(self):
        """
        Returns a numpy array containing the direct dimension ruler in Hz
        """
        sw = self.readacqpar("SW_h", True)
        si = self.readprocpar("SI", True)
        stsi = self.readprocpar("STSI", True)
        stsr = self.readprocpar("STSR", True)
        sf = self.readprocpar("SF", True)
        sfo1 = self.readacqpar("SFO1", True)
        hz = -sw/si*np.arange(-si/2, si/2)-(sfo1-sf)*1e6
        return hz[stsr:stsr+stsi]

    def getyhz(self):
        """
        Returns a numpy array containing the indirect dimension ruler in Hz
        (for 2D only)
        """
        sw = self.readacqpar("SW_h", True, 2)
        si = self.readprocpar("SI", True, 2)
        stsi = self.readprocpar("STSI", True, 2)
        stsr = self.readprocpar("STSR", True, 2)
        sf = self.readprocpar("SF", True, 2)
        sfo1 = self.readacqpar("SFO1", True, 2)
        hz = -sw/si*np.arange(-si/2, si/2)-(sfo1-sf)*1e6
        return hz[stsr:stsr+stsi]

    def getxppm(self):
        """
        Returns a numpy array containing the direct dimension ruler in ppm
        """
        sw = self.readacqpar("SW_h", True)
        si = self.readprocpar("SI", True)
        stsi = self.readprocpar("STSI", True)
        stsr = self.readprocpar("STSR", True)
        sf = self.readprocpar("SF", True)
        sfo1 = self.readacqpar("SFO1", True)
        ppm = -(sw/si*np.arange(-si/2, si/2)-(sfo1-sf)*1e6)/sf
        return ppm[stsr:stsr+stsi]

    def getyppm(self):
        """
        Returns a numpy array containing the indirect dimension ruler in ppm
        (for 2D only)
        """
        sw = self.readacqpar("SW_h", True, 2)
        si = self.readprocpar("SI", True, 2)
        stsi = self.readprocpar("STSI", True, 2)
        stsr = self.readprocpar("STSR", True, 2)
        sf = self.readprocpar("SF", True, 2)
        sfo1 = self.readacqpar("SFO1", True, 2)
        ppm = -(sw/si*np.arange(-si/2, si/2)-(sfo1-sf)*1e6)/sf
        return ppm[stsr:stsr+stsi]

def SInext(TD):
    """ Calculates the closest SI value (power of 2) directly larger than TD 
        TD can be scalar or iterable
        if iterable, return a list of ints
    """
    import numpy as np
    if type(TD) is int:
        return int(2**(np.ceil(np.log2(TD))))
    else:
        return [int(i) for i in 2**(np.ceil(np.log2(TD)))]

def zeroFill(spect, SI): 
    """ Zero fill a nDarray according to SI shape tuple.
        check for rank consistency between spect and SI
        for each dimension spect is zero padded on the right up to SI
        if SI size is lower than spect for a given dimension, than truncation occurs
    """
    import numpy as np
    if len(spect.shape) != len(SI):
        raise ValueError("spect (%dD) and SI (%dD) do not have the same number of dimensions:" % (len(spect.shape), len(SI.shape)))
    pad_size = []
    slice_required = False
    for dim_spect, dim_si in zip(spect.shape, SI):
        if dim_si< dim_spect:
            dim_si = dim_spect
            slice_required = True
        pad_size.append((0,dim_si-dim_spect))
    spect = np.pad(spect, pad_size, mode='constant')
    # now slice if required
    if slice_required:
        slicers = [slice(i) for i in SI]
        return spect[tuple(slicers)]
    else:
        return spect
