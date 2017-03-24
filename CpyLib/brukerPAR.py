## this bruker Cpython library requires numpy to manipulate arrays
## in particular this is true for reading 2D processed data that 
## have submatrix ordering (xdim) 
## therefore this cannot be used directly in topspin python scripts

## library will be distributed under GPLv3 once everything is working
## Copyright julien TREBOSC
## 01 jan 2011

## TODO : 3D or more dataset for read and write
##        improve processed data unit management
##        new function getprocunit
##        new function getprocx, getprocy automatically based on unit (s ppm Hz or other...)
##	- read title
##	- parser for status pulseprogram
##	- dictionary : parameter/parameter meaning/value

import sys
import os.path
import re


pyver=sys.version
print "python version : " + pyver

if pyver < "2.2" :
	print "python version : " + pyver
	raise "Error", "current version %s. version >= 2.2 required!" % pyver

def splitprocpath(path):
		"""
		extract [name,expno,procno,dir,user] from path to procno folder
		"""
		# make path absolute and normalised
		path=os.path.abspath(path)
		(path,procno)=os.path.split(path)
		(path,tmp)=os.path.split(path)
		if tmp!="pdata" : 
			print "wrong bruker data/procno path"
			return ""
		(path,expno)=os.path.split(path)
		(path,name)=os.path.split(path)
		list=[]
		# to be tested on Windows
		while path!='/':
			(path,tmp)=os.path.split(path)
			list.insert(0,tmp)
		if list[-1]=="nmr" and  list[-3]=="data" : 
			# we are in version <3
			list.pop()
			user=list.pop()
			list.pop()
			dir="/"+"/".join(list)
			dir=os.path.normpath(dir)
			return [name,expno,procno,dir,user]
		else : # this is version 3 without data/user/nmr format
			dir="/"+"/".join(list)
			return [name,expno,procno,dir]


class dataset:
	"""
	class to handle bruker datasets
	instanciation uses bruker style :
	a tuple containing [name,expno,procno,dir,user]
	variables:
	dataset : bruker way of defining datasets in a list [name, expno, procno, dir [, user]]
	version : 2 for topspin versions <3 and 3 for topspin versions >= 3
	bytencP : processed data byte encoding of dataset
	bytencA : raw data byte encoding of dataset
	methods :
	* =returnacqpath()                                           returns "string"
	* =returnprocpath()                                          returns "string"
	* =readacqpar("param",status=True(|False),dimension=1(|2))   returns "string"
	* =readprocpar("param",status=True(|False),dimension=1(|2))  returns "string"
	* =writeacqpar("param",value="0",status=True(|False),dimension=1(|2))   returns nothing
	* =writeprocpar("param",value="0",status=True(|False),dimension=1(|2))  returns nothing
	* =getdigfilt()                                              returns int
	TODO : 
	- read title
	- parser for status pulseprogram
	- dictionary : parameter/parameter meaning/value
	"""
	def __init__(self,set=['','','','','']):
		self.dataset=set
		# if list is 5 arguments then it's topspin version < 3
		# else it's topspin version 3
		if len(set)==5 : self.version=2
		if len(set)==4 : self.version=3

		if  not os.path.exists(self.returnacqpath()):
			print "Wrong dataset :\n" + self.returnacqpath() +" does not exist!!"

	def returnacqpath(self):
		"""
		returns folder pathway where acqu/fid files are stored (with "/" separators)
		"""
		if self.version==2 :
			path="%s/data/%s/nmr/%s/%s/" % (self.dataset[3],self.dataset[4],self.dataset[0],self.dataset[1])
			return path
		elif self.version==3: 
			path="%s/%s/%s/" % (self.dataset[3],self.dataset[0],self.dataset[1])
			return path
		else: 	return ""

	def returnprocpath(self):
		"""
		returns folder pathway where proc/1r/2rr... files are stored (with "/" separators)
		"""
		if self.version==2 :
			path="%s/data/%s/nmr/%s/%s/pdata/%s/" % (self.dataset[3],self.dataset[4],self.dataset[0],self.dataset[1],self.dataset[2])
			return path
		elif self.version==3: 
			path="%s/%s/%s/pdata/%s/" % (self.dataset[3],self.dataset[0],self.dataset[1],self.dataset[2])
			return path
		else: return ""

	def writeacqpar(self,param,value,status=True,dimension=1):
		"""
		write parameter "param" to acqu/acqus/acqu2/acqu2s
		if status=True writes "status" parameter (default)
		writes in file corresponding to dimension (default 1) 
		        acqu or acqus if dimension=1
			acqu2 or acqu2s if dimension=2
		returns True if success or False if parameter is not found. 
		User must convert the parameter to string
		Can write arrayed parameter with parameter array name and index in the array separated by a space
		e.g. : "P 1", "D 0"
		"""

		if dimension==1: name='acqu'
		elif dimension==2: name='acqu2'
		else :  
			print "Warning dimension must be 1 or 2 : using dimension 1"
			name='acqu'
		if status==True : name+='s'

		path=self.returnacqpath()+name

		if not os.path.exists(path): 
			print path +" does not exist!!"
			return None
		return self._writepar(path,param,value)

	def writeprocpar(self,param,value,status=True,dimension=1):
		"""
		writes parameter "param" from proc/procs/proc2/proc2s
		if status=True reads "status" parameter (default)
		writes in file corresponding to dimension (default 1) 
		        proc or procs if dimension=1
			proc2 or proc2s if dimension=2
		returns True if success or False if parameter is not found. 
		User must convert the parameter to string
		"""

		if dimension==1: name='proc'
		elif dimension==2: name='proc2'
		else : name='proc'
		if status==True : name+='s'


		path=self.returnprocpath()+name

		if not os.path.exists(path): 
			print path +" does not exist!!"
			return None
		return self._writepar(path,param,value)

	def readacqpar(self,param,status=True,dimension=1):
		"""
		reads parameter "param" from acqu/acqus/acqu2/acqu2s
		if status=True reads "status" parameter (default)
		reads in file corresponding to dimension (default 1) 
		        acqu or acqus if dimension=1
			acqu2 or acqu2s if dimension=2
		returns parameter as string or None if parameter is not found. 
		User must convert the parameter type himself if needed
		Can extract arrayed parameter with parameter array name and index in the array separated by a space
		e.g. : "P 1", "D 0"
		"""

		if dimension==1: name='acqu'
		elif dimension==2: name='acqu2'
		else :  
			print "Warning dimension must be 1 or 2 : using dimension 1"
			name='acqu'
		if status==True : name+='s'

		path=self.returnacqpath()+name

		if not os.path.exists(path): 
			print path +" does not exist!!"
			return None
		return self._readpar(path,param)

	def readprocpar(self,param,status=True,dimension=1):
		"""
		reads parameter "param" from proc/procs/proc2/proc2s
		if status=True reads "status" parameter (default)
		reads in file corresponding to dimension (default 1) 
		        proc or procs if dimension=1
			proc2 or proc2s if dimension=2
		returns parameter as string or None if parameter is not found. 
		User must convert the parameter type himself if needed
		"""

		if dimension==1: name='proc'
		elif dimension==2: name='proc2'
		else : name='proc'
		if status==True : name+='s'


		path=self.returnprocpath()+name

		if not os.path.exists(path): 
			print path +" does not exist!!"
			return None
		return self._readpar(path,param)

	def _readpar(self,path,param):
		"""
		reads parameter "param" from JCAMPDX file specified in path
		returns parameter as string or None if parameter is not found. 
		User must convert the parameter type himself if needed
		Can extract arrayed parameter with parameter array name and index in the array separated by a space
		e.g. : "P 1", "D 0"
		"""
		value=None
		t=param.split(' ')
		[searchString,pindex]=[-1,-1]
		if len(t)>1: [searchString,pindex]=t
		else:searchString=t[0]

		f=open(path,"r")
		ls= f.readlines()
		f.close()

		found=0
		for index in range(0,len(ls)-1):
			line=ls[index].strip()
			if line.find("##$"+searchString+"=")>-1: 
				#case of non array
				if pindex==-1:
					[tmp,value]=line.split('=')
					value=value.strip(" <>")
					found=1
					break
				# case of array
				else:
 					arraylist=[]
					matchres=re.search(r"\(0\.\.([0-9]+)\)",line)
 					if matchres:
 	  					maxindex=int(matchres.group(1))
#   						print "maxindex="+str(maxindex)
					else:
						print "sorry, "+searchString+" doesn't appear to be an array"
						return None


					[tmp,arrayed]=line.split(')')
					if not arrayed=='' :arraylist=arrayed.strip().split(' ')
					i=1
					line=ls[index+i].strip()
					while not line.startswith('#'):
						arraylist=arraylist+line.split(' ')
						i=i+1
						line=ls[index+i].strip()
					break
 		if pindex>-1:
			if int(pindex)<=int(maxindex):
				value=arraylist[int(pindex)]
				found=1
			else:
				print "sorry array list goes only up to "+str(maxindex)
	 			return None

 		if not found: 
 			print "sorry couldn't find param '"+searchString+"'"
 			return None
		return value

	def _writepar(self,path=None,param=None,value=""):
		"""
		changes parameter "param" to value in JCAMPDX file specified in path
		returns parameter as string or None if parameter is not found. 
		User must convert the parameter type himself if needed
		Can extract arrayed parameter with parameter array name and index in the array separated by a space
		e.g. : "P 1", "D 0"
		syntax : 
		##$STRING= <string>
		##$NUMBER= number
		##$ARRAY= (0..MAXINDEX)
		0 0 0 0 0 0 0 0 0 0 0 0 (max character 71 column, but can extend beyond if last value start on column 71)
		"""
		found=None
		# split the param. If more than one split then it's an array with an index else it's a scalar
		t=param.split(' ')
		[searchString,pindex]=[-1,-1]
		if len(t)>1: [searchString,pindex]=t
		else:searchString=t[0]

		f=open(path,"r")
		ls= f.readlines()
		f.close()
# look for param in ls then parse value or array
		for index in range(0,len(ls)-1):
			line=ls[index]
			if line.find("##$"+searchString+"=")>-1: 
				#case of non array
				if pindex==-1:
					if line.find('\<')>=0: 
						value="<"+value+">"
					line="##$"+searchString+"= "+value+"\n"
					ls[index]=line
					found=1
					break
				# case of array
				else:
 					arraylist=[]
					# maxindex contains max index from ##$ARRAY= (0..MAXINDEX)
					matchres=re.search(r"\(0\.\.([0-9]+)\)",line)
 					if matchres:
 	  					maxindex=int(matchres.group(1))
#   						print "maxindex="+str(maxindex)
					else:
						print "sorry, "+searchString+" doesn't appear to be an array"
						return False

					#read all array values
					i=1
					line=ls[index+i].strip()
					while not line.startswith('#'):
						arraylist=arraylist+line.split(' ')
						i=i+1
						line=ls[index+i].strip()
					max_i=i
					if (len(arraylist) > int(pindex)) : found=1
					# delete lines index+1 to index+i-1 included
					del ls[index+1:index+max_i]
					# change the correponding value
					if int(pindex)<=int(maxindex):
						arraylist[int(pindex)]=value
						arraystring=" ".join(arraylist)
						maxchar=72
						i=1
						arrayst=[]
						while len(arraystring)>maxchar :
							splitindex= arraystring.rfind(" ",0,maxchar)
							arrayst.append(arraystring[0:splitindex]+"\n")
							arraystring=arraystring[splitindex:].lstrip()
							i=i+1
						arrayst.append(arraystring+"\n")
						# at this point one need to insert i lines after index
						for j in range(i):
							ls.insert(index+1+j,arrayst[j])
					else:
						print "sorry array list goes only up to "+str(maxindex)
			 			return False
					break

 		if not found: 
 			print "sorry couldn't find param '"+searchString+"'"
 			return False
		
		# write the file back
		f=open(path,"w")
		f.write(''.join(ls))
		f.close()
		return True

	def getdigfilt(self):
		"""
		returns the number of points that corresponds to 
		digital filter artifact in a fid/ser file
		Only returns value stored in GRPDLY for now
		TODO : account for other DSP firmware versions
		"""
		tabgrpdly= {
			'10': 	{
				'2': '44.7500',
				'3': '33.5000',
				'4': '66.6250',
				'6': '59.0833',
				'8': '68.5625',
				'12': '60.3750',
				'16': '69.5313',
				'24': '61.0208',
				'32': '70.0156',
				'48': '61.3438',
				'64': '70.2578',
				'96': '61.5052',
				'128': '70.3789',
				'192': '61.5859',
				'256': '70.4395',
				'384': '61.6263',
				'512': '70.4697',
				'1024':	'70.4849',
				'1536': '61.6566',
				'2048': '70.4924',
				'768': '61.6465'
				},
			'11':	{
				'2': '46.0000',
				'3': '36.5000',
				'4': '48.0000',
				'6': '50.1667',
				'8': '53.2500',
				'12': '69.5000',
				'16': '72.2500',
				'24': '70.1667',
				'32': '72.7500',
				'48': '70.5000',
				'64': '73.0000',
				'96': '70.6667',
				'128': '72.5000',
				'192': '71.3333',
				'256': '72.2500',
				'384': '71.6667',
				'512': '72.1250',
				'768': '71.8333',
				'1024': '72.0625',
				'1536': '71.9167',
				'2048': '72.0313'
				},
			'12': 	{
				'2': '46.3110',
				'3': '36.5300',
				'4': '47.8700',
				'8': '53.2890',
				'6': '50.2290',
				'12': '69.5510',
				'16': '71.6000',
				'24': '70.1840',
				'32': '72.1380',
				'48': '70.5280',
				'64': '72.3480',
				'96': '70.7000',
				'128': '72.5240',
				'192': '0.0000',
				'256': '0.0000',
				'384': '0.0000',
				'512': '0.0000',
				'768': '0.0000',
				'1024':	'0.0000',
				'1536': '0.0000',
				'2048': '0.0000'
				}
			}


		dspfirm=int(self.readacqpar("DSPFIRM",True))
		digtyp=int(self.readacqpar("DIGTYP",True))

		decim=self.readacqpar("DECIM",True)
		dspfvs=int(self.readacqpar("DSPFVS",True))
		digmod=int(self.readacqpar("DIGMOD",True))

		if digmod==0 : return 0
		if dspfvs>=20 : return float(self.readacqpar("GRPDLY",True))
		if ((dspfvs==10) | (dspfvs==11) | (dspfvs==12)): return tabgrpdly[str(dspfvs)][decim]
		print "DSPFVS="+str(dspfvs)+" not yet implemented"
		return None




