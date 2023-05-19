# -*- coding: utf-8 -*-
# this Cpython library requires numpy to manipulate arrays
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

import numpy as np

# for each dimension there as :
meta_fields = {'domain', 'multiplex', 'SWh', 'carrier_f', 'reference_f', 'name'}
# domain : 'time'| 'frequency' | other (power, experiment, optimized parameter)
# multiplex : holds hypercomplex or multiplex size: QF-> 1, States, 
#                States-TPPI...-> 2, others could be 4 or 6
# how to deal with sparse sampling ? Applies to time domain only
# other would also need a list of values

class NmrData:
    """ A class that handles nD NMR data with associated meta-data (dimensions,
        quadrature, domain (freq/time), axes...)
        Data stored as ndarray [dim_0, HC_0, dim_1, HC_1, ..., dim_-1, -HC_-1]
        Each dimension span 2 axes: one with TDn evolution and one with 
        hypercom/multip-lex data (HCsize size) with HC size depending on 
        hypercomplex acquisition:
        HC size = 1 if QF, = 2 if States, States_TPPI, more if multiplex
        Rephasing along one dimension will use last dim in case of HC size = 1
        classe attributes:
            data_array: the ndarray containing data with shape
                [dim_0, HC_0, dim_1, HC_1, ..., dim_-1, -HC_-1]
                where HC is the hyper complex/multiplex dimension associated with 
                corresponding axis.
                dimension -1 correspond to direct dimension
            dim_meta: an array with meta data for the dimensions store in dictionnary
                dict entries: 'type':'time'|'freq'|None, 'dim_size', 'multiplex',
                              'SWh', 'axis_name', carrier (original carrier frequency),
                              ref (reference frequency), offset (ppm position of 
                              high freq.). 
    """

    def __init__(self, data, metadata):
        data_array = data  # shape is Fn,HCn, ..., F1, HC1 with 1 direct dimension
        dim_meta = [] # for each dimension a dict with type (time/freq/None), hypercomplex/multiplex size, SWh, axis_name...
        pass

    def rephase_axis(self, axis=1, ph0=0, ph1=0, pivot1=0, ph2=0, pivot2=0):
        """Rephase data_array complex data along given axis [default 1].

            --- input ---
            axis: dimension to rephase. It can be an axis number 
                (as accessed by [-2*dim] in data_array  or
                a dimension name as found in dim_meta dict['axis_name'] 
                    (to be implemented)
                default is 1 that is direct dimension 
            ph0: the 0th order phase in degree (default=0)
            ph1: the 1st order phase in degree (default=0)
            pivot1: point index along axis that does not dephase with ph1
            ph2: the 2nd order phase in degree (default=0)
            pivot2: 2nd pivot point that does not dephase (along with pivot 1) 
                    with ph2
            for topspin compatibility pivot indexes for frequency are from high 
                to low frequency 
            (index 0 is highest frequency, and time 0)
        """
        if type(axis) is str:
            #search for dim axis according to name
            raise ValueError("not implemented yet")
        if dim_meta[-axis]['HCsize'] == 2:
            Re_idx = [slice(None)]*myarray.ndim
            Re_idx[-2*axis+1] = 0
            Im_idx = Re_idx.copy()[-2*axis+1] = 1
        else: # use the direct dimension complex number
            Re_idx = [...,0]
            Im_idx = [...,1]
        i = np.arange(self.data_array.shape[-2*axis])
        cosphi = np.cos(np.pi*(ph0+ph1*(i-pivot1)+ph2*(i-pivot1)*(i-pivot2))/180)
        sinphi = np.sin(np.pi*(ph0+ph1*(i-pivot1)+ph2*(i-pivot1)*(i-pivot2))/180)
        (data_array[Re_idx], data_array[Im_idx]) = (data_array[Re_idx]*cosphi - 
                  data_array[Im_idx]*sinphi,        data_array[Re_idx]*sinphi + 
                  data_array[Im_idx]*cosphi)

    def fft(self, axis):
        if 'time' not in self.meta[-axis]['type']:
            raise ValueError("axis type is not time. Cannot use fft")
        self.data_array = np.fft.fftshift(np.fft.fft(self.data_array, axis=-2*axis))
        self.meta[-axis]
        # update the metadata (axis, types)
        pass

    def ifft(self, axis)
        pass

    def zero_fill(self, size, axis):
        pass

    def apod(self, axes, lbs, slopes, initial_centers, functions):
        """ Applies apodization along 1 of more axes
            -- inputs -- 
                axes: axis or list of axes 
                lbs: broadening to apply (FWHM)
                slopes: center of apodization can move along axes to follow t2=Rxt1
                initial_centers: initial_center 
                functions : predefined functions or user function object
        """
        pass

    def shear(self, axes, ratio):
        """ Shear spectrum : axes[0] cols move w.r.t. ratio * axes[1]
            -- inputs --
                axes: axes[0] slides according to ratio w.r.t. axes[1]
                ratio: slope of shearing axes[0] = ratio axes[1]
        """
        pass
    
