# -*- coding: utf-8 -*-
# read popt protocol for automatic assignment of 2D stored optimization.
# Copyright Julien TREBOSC 2011, 2012
## Licence:
###    This program is free software: you can redistribute it and/or modify
###    it under the terms of the GNU General Public License as published by
###    the Free Software Foundation, either version 3 of the License, or
###    (at your option) any later version.
###
###    This program is distributed in the hope that it will be useful,
###    but WITHOUT ANY WARRANTY; without even the implied warranty of
###    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
###    GNU General Public License for more details.
###
###    You should have received a copy of the GNU General Public License
###    along with this program.  If not, see <http://www.gnu.org/licenses/>


"""
A module that parse popt.protocol file to extract what parameters were optimized

Implements a PoptProtocol class (input is the readlines() of popt.protocol file
Reports:
PoptProtocol is split in reports (stored in a Report Class). A report is what is stored whenever poptau is launched.
The report may have stored FIDs in a ser file (path is in Report.serDir)

Each report is split in Procno (several optimization in one poptau run)
For each procno one lists the optimized parameters, their values, the overall table of experiments

Optimized parameters are stored in params list of dict :
    params dict keys are (name, values, optmode, optgroup)
    tableIndex is a list of dict that stores the index of the experiment with the corresponding parameters values
    keys of the dict are 'index' and the parameter names

Data access through PoptProtocol.reports[i].procnos[j].params[k]['name'|'values'|'optmode']
Data access through PoptProtocol.reports[i].procnos[j].params[k]['values']
Data access through PoptProtocol.reports[i].procnos[j].tableIndex[k]['index'|'params[l]['name']]

"""
from __future__ import division, print_function
import numpy as n

# split popt.protocol in poptau reports in Report list


class PoptProtocol:
    """ 
    Parse a popt.protocol file then split it into reports
    class variables: 
        reports : a list of Report instances
    """
    def __init__(self, lines):
        """ splits a popt.protocol into reports lines. Reports are splitted according to the line starting with Report
        """    
        #search index where a report starts in lines 
        ls = [] # list with index of start of report
        i = 0
        for l in lines :
            if l.find("Report") == 0 : ls.append(i)
            i += 1
        ls.append(len(lines)) # appends the last line as last index

        self.reports = []
        for i in range(len(ls)-1):
            self.reports.append(Report(lines[ls[i]:ls[i+1]]))
        

class Report:
    """ 
    Parse a Report lines then split it into procnos
    class variables: 
        procnos : a list  of Procno instances
        serDir : path to dataset where 2D fids are stored
    """
    def __init__(self, lines):
        self.lines = lines
        # retrieve the name of expno where 2D ser is stored
        for l in lines:
            if l.find("Target directory for serfile:") == 0:
                self.serDir = l.split(':')[1].strip()

        #split report in procnos
        #search index where a procno starts in lines 
        ls = [] # list with index of start of procno
        i = 0
        for l in lines :
            if l.find("PROCNO=") == 0 : ls.append(i)
            i += 1
        self.procnos = []
        if len(ls) == 0 : return # there is no procno
        ls.append(len(lines)) # appends the last line as last index

        for i in range(len(ls)-1):
            self.procnos.append(Procno(lines[ls[i]:ls[i+1]]))


class Procno:
    """ 
    Parse a Procno lines to extract the optimized parameters
    class variables: 
        procno : the procno number where optimization is done
        params : a list containning the optimized parameters
            params[i] is a dict with keys (name, values, optmode, optgroup)
                name : name of the parameter
                values  list of values that parameter takes
                optmode : mode of optimization : Step, Array, Simult
                optgroup : Param group for Array or Simul
        tableIndex : an list giving the {index, param[:].value} of the actually done experiments
    """

    def __init__(self, lines):
        self.lines = lines
        #store the number of procno
        self.procno = lines[0].split('=')[1]
        self.params = []
        self.tableIndex = []
        tableStart = -1
        tableStop = -1
        # get the parameters names, type and range then calculates the list of values
        for i in range(len(lines)):
            if lines[i].find("Linear optimization of") == 0 or lines[i].find("Logarithmic optimization of") == 0 :
                var = lines[i].split()
                varmode = var[0]    
                if var[4] == "in" : # parameter is not array (e.g. RG) in one word
                    varname = var[3]
                    valsteps = var[5]
                    optmode = var[8]
                    optgroup = var[-1]
                else : # parameter is array (e.g. P 10) in two words
                    varname = " ".join(var[3:5])
                    valsteps = var[6]
                    optmode = var[9]
                    optgroup = var[-1]
                valstart = float(lines[i+1].split()[2])
                valstop = float(lines[i+1].split()[4])
                if varmode == 'Linear' : vals = n.linspace(valstart, valstop, num=valsteps)
                if varmode == 'Logarithmic' : vals = n.logspace(valstart, valstop, num=valsteps)
                # print(valsteps, varname, varmode, optmode, optgroup, vals)
                self.params.append({'name':varname, 'values':vals, 'optmode':optmode, 'optgroup':optgroup})
            if lines[i].find('Experiment') == 0 : 
                tableStart = i
            if lines[i].find('poptau for') == 0 :
                tableStop = i
                break
        if tableStart == -1 or tableStop == -1: return # tableIndex was not stored (if poptstop was used for example)

        for l in lines[tableStart+1:tableStop]:
            ls = l.strip().split("  ")
            for i in range(ls.count('')):
                ls.remove('')
            self.tableIndex.append({'index':int(ls[0])-1})
            for j in range(len(self.params)):
                self.tableIndex[-1][self.params[j]['name']] = float(ls[j+1])
	    
if __name__ == "__main__":
    import sys
    f = open(sys.argv[1])
    lines = f.readlines()
    A = PoptProtocol(lines)
    print([x['name'] for x in A.reports[-1].procnos[-1].params])
    print([x.procnos for x in A.reports])
    #print(A.reports[-1].procnos[-1].tableIndex)
    #
    # OK table read now I need to turn it in nD array, or just pass the params in right order


