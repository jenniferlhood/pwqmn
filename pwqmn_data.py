from __future__ import division
import csv
import sys, os
import warnings

from collections import Counter
from contextlib import contextmanager
from math import radians, cos, sin, asin, sqrt,log
from random import choice


#rpy2 libraries for accessing functionaity of R
from rpy2.robjects.packages import importr
from rpy2 import robjects
with warnings.catch_warnings():
	warnings.simplefilter("ignore")
	from rpy2.robjects.lib import ggplot2

#graphical output support
grdevices = importr('grDevices')
base = importr('base')
hmisc = importr('Hmisc')


# from:  http://thesmithfam.org/blog/2012/10/25/temporarily-suppress-console-output-in-python/
# used to suppress the "helpful suggestions" spam printed to consol by R's histogram function
@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout
	
	
"""-------------------
Supporting city class
--------------------"""

class city():
	def __init__(self,name,lat,lon):
		self.name = name
		self.latitude = lat
		self.longitude = lon


"""
==========================================
Class for housing each station's meta data  
==========================================
"""
class station():
	
	def __init__(self, name,number,latitude,longitude):
		#site attributes
		self.name = name
		self.number = number
		self.latitude = latitude
		self.longitude = longitude
		self.data = {}

		## the main data dictionary
		self.dataCols = {} 
		self.fidDate = {}
				
		#generate a blank data dictionary to recieve data from file
		self.data['PARM'] = []
		self.data['DATE'] = []
		self.data['RESULT'] = []
		self.data['FID'] = []
		self.data['REMARK'] = []
		self.data['METHOD'] = []
		self.data['UNIT'] = []
		self.data['STATION'] = []

	#called on the site for each new file that is read					
	def add_data(self,rowList):

		self.data['PARM'].append(rowList[0])
		self.data['DATE'].append(rowList[1])
		self.data['RESULT'].append(rowList[2])
		self.data['FID'].append(rowList[3])
		self.data['REMARK'].append(rowList[4])
		self.data['METHOD'].append(rowList[5])
		self.data['UNIT'].append(rowList[6])
		self.data['STATION'].append(rowList[7])


	def checkData(self): #check that the length of all the column arrays is of consistent size
		if len(self.data['PARM']) == len(self.data['DATE']) == len(self.data['RESULT']) \
			== len(self.data['FID']) == len(self.data['REMARK']) == len(self.data['METHOD']) \
			== len(self.data['UNIT']): 
			return True
			
		else: return False
		
	
	def getUnits(self,parm): #finds the units of particular paramter
		location = self.data['PARM'].index(parm)
		return self.data['UNIT'][location]
	
	
	def getMethod(self,parm): #finds the method of particular paramter
		location = self.data['PARM'].index(parm)
		return self.data['METHOD'][location]
		
	
	def toString(self):
		return "Site: %s (%s), has %s observations" %(self.name, 
			self.number, self.numberOfObs())
			
			
	""" 
	The PWQMN data comes organized where each parameter is listed as an obervation, 
	each observation a row.	Each sampling date, multiple paramters are measured 
	at each station, but not every parameter at every stationat each sampling date.
	This means there are from 0 to ~190 observations made for any given date and station.
	Thus, data reorganization and replacement of missing values with Null entries 
	is necessary for paired sample stats and graphs.
		
	 The new observation dictionary follows a specified format such that data associated
	 with each paramter can be accessed using the paramter as the key:
	 	
	 	{[parm]:[[date, fid, result, unit, method, station],[]...[]] 
	"""
	
	def parmToCols(self):
		index = 0
		fidCheck = {}
		
		for i in self.data['PARM']:
			
			if i not in fidCheck:
				fidCheck[i] = []
						
			if self.data['FID'][index] not in fidCheck[i]:
				if i in self.dataCols:
					self.dataCols[i].append([self.data['DATE'][index],self.data['FID'][index], \
						self.data['RESULT'][index],self.data['UNIT'][index], \
						self.data['METHOD'][index],self.data['STATION'][index]])
				else:
					self.dataCols[i] = []
					self.dataCols[i].append([self.data['DATE'][index],self.data['FID'][index], \
						self.data['RESULT'][index],self.data['UNIT'][index], \
						self.data['METHOD'][index], self.data['STATION'][index]])

			fidCheck[i].append((self.data['FID'][index]))
					
			#create the dictionary that contains all FIDs and dates. Used to determine null placement.
			if self.data['FID'][index] not in self.fidDate:
				self.fidDate[self.data['FID'][index]] = self.data['DATE'][index]
				
			index += 1
		
		## fill in nulls (None) for missing measurements
				
		for i in self.dataCols: ## each i parameter
			fidPresent = False
			for k in self.fidDate: # go through all FIDs that any observation was made
				for j in self.dataCols[i]: #go through each observation list
					if k in j: #element 1 if the observatio list is the FID
						fidPresent = True						
				if fidPresent == False:
					self.dataCols[i].append([self.fidDate[k],k,None,None,None,None])		
	
				fidPresent = False	
					

	"""------Methods on transformed data-----------"""	
		
	def setOfParms(self):
		return {i for i in self.data['PARM']} # returns a set
		
	def setOfUnits(self):
		return {i for i in self.data['UNIT']}
			
	def numberOfParms(self):
		return len(self.setOfParms())
		
	def numObs(self):
		return len(self.fidDate)

	def parmCountAll(self):
		parmDict = {}
		for i in self.data['PARM']:
			if i in parmDict:
				parmDict[i] += 1
			else:
				parmDict[i] = 1
		return parmDict

	def parmCount(self,parm):
		count = 0
		if parm in self.dataCols:
			count = self.parmCountAll()[parm]
		
		return count 

	def numberOfDates(self):
		return len(self.fidDate)
		
	def setOfYears(self):
		return {self.fidDate[i][0] for i in self.fidDate}
				
	def parseDate(self):
		newFidDate = {}
		for i in self.fidDate:
			#if the date has already been parsed, 
			# a type error will be thrown. In this case, just do nothing

			try:
				year = int(self.fidDate[i][0:4])
				month = int(self.fidDate[i][5:7])
				day = int(self.fidDate[i][8:10])
				
				newFidDate[i] = (year,month,day)
				
			except TypeError:
				newFidDate = None
			
		if newFidDate != None:
			self.fidDate = newFidDate
	
		

"""
---------------------------------------------------------------------------
Main class for housing all station objects
Most program methods (including stats and graphics) operate on this object
---------------------------------------------------------------------------
"""

class allStationData():
	def __init__(self,stFileName):
		self.stationDict = {}
		self.selectParm = []
		self.selectYear = []
		self.cityDict = {}
		
		if stFileName != None:		
			with open(stFileName) as csvfile:
				allStations = csv.reader(csvfile, delimiter = ",", quotechar = '"')
				for row in allStations:
					#stationList.append(station(row[1],row[0],row[3],row[2]))
					if row[0] != 'STATION': # don't add the headers as a station object
						self.stationDict[int(row[0])] = station(row[1],int(row[0]), \
							float(row[3]),float(row[2]))
			

		
	def getStationData(self,fileName):
		with open(fileName) as csvfile:
			allData = csv.reader(csvfile, delimiter = ",", quotechar = '"')
			for row in allData:
				if row[0] != 'STATION': # don't add the headers to the data
					#create a list of the current row to add to the current station
					#in order: PARAM,DATE,RESULT,FID,REMARK,METHOD,UNIT
					rowList = [row[1],row[3],float(row[7]),row[5],row[6],row[9],row[10],row[0]]
					self.stationDict[int(row[0])].add_data(rowList)
	
	def getCities(self,filename):
		cityfile=open(filename).read().split('\n')
		for i in cityfile:
			if len(i.split(',')) == 3:
				cityList=i.split(',')
				self.cityDict[cityList[0]]=city(cityList[0],float(cityList[1]),float(cityList[2]))
				
		
	##
	# All station data must be reorganized after loading!		
	##
	def allReorganize(self):
		for s in self.stationDict:
			self.stationDict[s].parmToCols()
			
			self.stationDict[s].parseDate()
	
	""" ---------------------------------------------------------------------
	Methods to relaplace labels for increased readablility
	 
	-----------------------------------------------------------------------""" 
	#collect the set of all units to replace them with abbreviated versions (temp)
	#this function is for graph aesthetics
	def getUnits(self,parm):
		for i in self.stationDict:
			if parm in self.stationDict[i].setOfParms():
				return self.unitReplace(self.stationDict[i].getUnits(parm))

				
	def setOfUnits(self):
		units = set()
		unitDict = {}
		
		for i in self.stationDict:
			units = units | self.stationDict[i].setOfUnits()
		return units
		

	#returns a new unit string with condensed units 
	def unitReplace(self, unit):
		if unit == "NO DIMENSION/SCALE":
			return " "
		elif unit == "MICROGRAM PER LITER":
			return "ug/l"
		elif unit == "NANOGRAM PER LITER":
			return "ng/l"
		elif unit == "MILLIGRAM PER LITER":
			return "mg/l"
		elif unit == "MICROMHOS/CM (CONDUCTIVITY)":
			return "uS/cm"
		elif unit == "MICRO SIEMENS PER CENTIMETER":
			return "uS/cm"
		elif unit == "BECQUEREL PER LITRE":
			return "Bq/l"
		elif unit == "FORMAZIN TURBIDITY UNIT":
			return "FTU"
		elif unit == "TRUE COLOUR UNITS (TCU)":
			return "TCU"
		elif unit == "DEGREES CELSIUS":
			return "C"
		elif unit == "MILLIEQUIVALENTS/LITER":
			return "mEq/l"
		elif unit == "COUNTS":
			return "count"
		else:
			 return unit
			 
	
	#takes a list of month strings, returns a list of equal length with months converted to seasons
	def toSeason(self,month):
		seasons = []
		for i in month:
			if i == "12" or i == "01" or i == "02":
				seasons.append("Winter (Dec, Jan, Feb)")
			elif i == "03" or i == "04" or i == "05":
				seasons.append("Spring (Mar, Apr, May)")
			elif i == "06" or i == "07" or i == "08":
				seasons.append("Summer (Jun, Jul, Aug)")	
			elif i == "09" or i=="10" or i=="11":
				seasons.append("Fall (Sep, Oct, Nov)")
			else:
				seasons.append(i)
		return seasons
		
	
	"""---------------------------------------------------
	Methods for generating a subset of all stations.
		subset methods return a new allStationData object
		or append to an exisitng one.
	-----------------------------------------------------"""
	
	#haversine method to compute distance in km between two stations		
	def haversine(self,S1,S2):
		lon1,lat1,lon2,lat2 = map(radians, [S1.longitude, S1.latitude, S2.longitude, S2.latitude])
		
		dlon = lon2-lon1
		dlat = lat2-lat1
		a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
		c = 2 * asin(sqrt(a))
		#radius of the earth is 6371 km
		return c * 6371 
	
	
	#create a new selected allstations object	
	def selectRiver(self, river):
		newStationDict = {}
		newStationSelect = allStationData(None)
		
		if river in self.countAllRivers():
			for i in self.stationDict:
				if self.stationDict[i].name == river:
					newStationDict[i] = self.stationDict[i]
		
		newStationSelect.stationDict = newStationDict
		newStationSelect.selectParm = self.selectParm
		newStationSelect.selectYear = self.selectYear
		
		return newStationSelect
	
	
	#append to the existing selected allstations object.
	#  Must pass the selected station object as parameter
	def addRiver(self, other, river):
		if river in self.countAllRivers():
			for i in self.stationDict:
				if self.stationDict[i].name == river:
					other.stationDict[i] = self.stationDict[i]
					
	
	def removeRiver(self, other, river):
		toDelete = {}
		if river in other.countAllRivers():
			for i in other.stationDict:
				if other.stationDict[i].name == river:
					toDelete[i] = other.stationDict[i]
			for j in toDelete:
				del other.stationDict[j]
		
	
	def selectCity(self, city, km):
		newStationDict = {}
		newStationSelect = allStationData(None)
		
		if city in self.cityDict:
			for i in self.stationDict:
				if self.haversine(self.stationDict[i],self.cityDict[city]) <= km:
					newStationDict[i] = self.stationDict[i]
		
		newStationSelect.stationDict = newStationDict
		newStationSelect.selectParm = self.selectParm
		newStationSelect.selectYear = self.selectYear
		
		return newStationSelect

	#remove stations that have zero observations for selected parameters
	# this function should only be called on a selectedData allStationsData object.
	# (otherwise data will be lost, will need to be reloaded).
	def removeZeros(self):
		removeList = []
		if self.selectParm != None:
			for i in self.selectParm:
				for j in self.stationDict:
					if self.stationDict[j].parmCount(i) == 0:
						if j not in removeList:
							removeList.append(j)
		
		for k in removeList:
			del self.stationDict[k]
			
			
				
	#removes stations that have observations below a threshold		
	def removeLow(self,n):
		removeList = []
		if self.selectParm != None:
			for i in self.selectParm:
				for j in self.stationDict:
					if self.stationDict[j].parmCount(i) < n:
						if j not in removeList:
							removeList.append(j)
		for k in removeList:
			del self.stationDict[k]
		
			
			
			
	"""-------------------------------------------------------------
	Methods that produce lists and descriptions of all/selected stations 

	-------------------------------------------------------------"""	
	
	def numOfStations(self):
		return len(self.stationDict)
	
	
	def numObs(self):
		count = 0
		for i in self.stationDict:
			count += self.stationDict[i].numObs()
		return count
		

	def setOfStations(self):
		return {i:self.stationDict[i].name for i in self.stationDict}
	
	
	#returns a dict with counts for stations per river
	def countAllRivers(self):
		riverDict={}
		for i in self.stationDict:
			if self.stationDict[i].name in riverDict:
				riverDict[self.stationDict[i].name] +=1
			else:
				riverDict[self.stationDict[i].name] = 1
				
		return riverDict
	
	#returns a dict with counts for observations per river, per parameter
	def countAllRiverParm(self,parm):
		riverDict={}
		if parm in self.setOfParms():
			for i in self.stationDict:
				if self.stationDict[i].name in riverDict:
					riverDict[self.stationDict[i].name] += self.stationDict[i].parmCount(parm)
				else:
					riverDict[self.stationDict[i].name] = self.stationDict[i].parmCount(parm)
		return riverDict		
				

	def setOfParms(self):
		parms = set()
		for i in self.stationDict:
			parms = parms | self.stationDict[i].setOfParms()
			
		return parms	
	
	
	#returns a dictionary with the the number of observations of each parameter
	def countAllParm(self): 
		parmDict = Counter()
		for i in self.stationDict:
			parmDict += Counter(self.stationDict[i].parmCountAll())
		return dict(parmDict)
	

	#returns the dict of the selected parms and counts
	#(may not be necessary)
	def countSelectParm(self):
		allParmDict = self.countAllParm()
		selectParmDict = {}
		
		if self.selectParm != None and allParmDict != {}:
			
			for i in self.selectParm:
				if i in allParmDict:
					selectParmDict[i] = allParmDict[i]
				else:
					selectParmDict[i] = 0
					
		return selectParmDict
		
	
	#returns the count of selected parm
	def countParm(self,parm):
		return self.countAllParm()[parm]		
	
	
	def topParm(self, n):
	
		if n > len(self.setOfParms()):
			n = len(self.setOfParms())
		elif n < 1:
			n = 1

		countList = self.countAllParm().items()
		countList.sort(key=lambda countList:countList[1], reverse = True)	

		return dict([countList[i] for i in range(0,n)])
		

	def setOfYears(self):
		years = set()
		for i in self.stationDict:
			years = years | self.stationDict[i].setOfYears()
		return years
	
	
	"""------------------------------------------------
	Methods to change the selected parameters and years
	------------------------------------------------"""
	#qsort increasing: removes nulls and NA objects
	def sort1(list1):
		if len(list1) == 1:
			return list1
		else:
			partition = len(list1)/2
			one = list1[0:part]
			two = list1[part:]
			if one[0] < two[0]:
				return sort1(one) + sort1(two)
			else:
				return sort1(two) + sort1(one)
		
		
	def selectTopParm(self,n):
		self.selectParm = self.topParm(n).keys()	
		
	def addParm(self, parm):
		if parm in self.countAllParm() and parm not in self.selectParm:
			self.selectParm.append(parm)
			
	def removeParm(self,parm):
		if parm in self.selectParm:
			self.selectParm.remove(parm)
			
	def selectYears(self):
		self.selectYear = [i for i in self.setOfYears()]
	
	def addYear(self, year):
		if year in self.setOfYears() and year not in self.selectYear:
			self.selectYear.append(year)
	
	def removeYear(self, year):
		if year in self.selectYear:
			self.selectYear.remove(year)
			
			
	"""-------------------------------------------------------
	Basic stats functions. Takes an R vector column or a list) 
	------------------------------------------------------- """
	
	#quick sort that removes nulls and R NA objects
	def qsort(self,a):
		if len(a) == 0:
			return []
		x = choice(a)
		while x == None or x is robjects.NA_Real:
			x = choice(a)
		l = [i for i in a if i < x and i != None and i != robjects.NA_Real]
		e = [i for i in a if i == x]
		g = [i for i in a if i > x and i != None and i != robjects.NA_Real]
		return self.qsort(l) + e + self.qsort(g)
	
	
	def mean(self,data):
		#sums = reduce(lambda x,y: x+y if x != None and y != None else x,data)
		n = 0
		sums = 0
		for i in data:
			if i != None and i != robjects.NA_Real:
				sums +=i
				n+=1
		if n != 0:
			return sums/n
		else: 
			return 0
	
	
	def median(self,data):
		#sort data and remove Nulls
		data = self.qsort(data)
		n = len(data)
		
		#separate case for even and odd n
		if n > 2:
			if n % 2 == 0:
				medn = (data[int(n/2)] + data[int(n/2)-1])/2
			else:
				medn = data[int(n/2)]
		elif n == 2:
			medn = sum(data)/2
		elif n == 1:
			medn = data[0]
		else:
			medn = 0
		return medn
		
		
	def stdev(self,data):
		diffs = 0
		n = 0
		mean = self.mean(data)
		for i in data:
			if i != None and i != robjects.NA_Real:
				diffs += (i - mean)**2
				n+=1
		if n != 0:
			return sqrt(diffs/(n-1))
		else:
			return 0
			
	#determine skewness on a data column
	def skewness(self,data):
		cubediffs = 0
		mean = self.mean(data)
		std = self.stdev(data)
		n = 0
		for i in data:
			if i != None and i != robjects.NA_Real:
				cubediffs += (i- mean)**3
				n+= 1
		if n != 0 and std != 0:				
			m3 = cubediffs/n
			return m3/(std**3)
		else:
			return 0
		
	def pearsons(self,parm1,parm2):
		vectorDict = {}
		dataframe = self.getSelectParmData()
		names =dataframe.names
		
		vectorDict[parm1] = dataframe[names.index(parm1)]
		vectorDict[parm2] = dataframe[names.index(parm2)]
		
		if self.skewness(vectorDict[parm1]) > 1 or self.skewness(vectorDict[parm1]) < -1:
			vectorDict[parm1] = base.log10(vectorDict[parm1])
			
		if self.skewness(vectorDict[parm2]) > 1 or self.skewness(vectorDict[parm2]) < -1:
			vectorDict[parm2] = base.log10(vectorDict[parm2])
		
		newDataframe = robjects.DataFrame(vectorDict)
		
		matrix = base.as_matrix(newDataframe)
		cor = hmisc.rcorr(matrix,type="pearson")
		
		#return stats.cor(newDataframe,use="pairwise.complete.obs",method="pearson")
		
		#return the correlation coeeficient and the p-value as extracted from the resulting matrix
		return cor[0][1],cor[2][1]
		
	#produce a summary of selected data to be printed to
	# screen or to file. Returns a dict with the following:
	# {[Parm]:[n,mean, median, standard deviation]}
	def summary(self):
		dataframe = self.getSelectParmData()
		names = dataframe.names
		summaryDict = {}

		
		for i in self.selectParm:
			if i in self.setOfParms():
				parmVector = dataframe[names.index(i)]
				summaryDict[i] = []
				sortList = list(self.qsort(parmVector))
		
				summaryDict[i].append(len(sortList))
				summaryDict[i].append(round(self.mean(parmVector),4))
				summaryDict[i].append(round(self.median(parmVector),4))
				summaryDict[i].append(round(self.stdev(parmVector),4))
				
		return summaryDict
		
	"""
	==========================
	R Dataframes and graphics
	==========================
	"""
	
	def stationsDataFrame(self): # produce a data frame of station data
		vectorDict = {}
		currentList = [[],[],[],[]] # build a list of stations,names,lat and long: A (4xn) 2d list
		
		for i in self.stationDict:
			currentList[0].append(i)
			currentList[1].append(self.stationDict[i].name)
			currentList[2].append(self.stationDict[i].latitude)
			currentList[3].append(self.stationDict[i].longitude)

		vectorDict['Station'] = robjects.StrVector(currentList[0])
		vectorDict['Name'] = robjects.StrVector(currentList[1])
		vectorDict['Latitude'] = robjects.StrVector(currentList[2])
		vectorDict['Longitude'] = robjects.StrVector(currentList[3])
		
		return robjects.DataFrame(vectorDict)
		
	def getSelectParmData(self):
		vectorDict = {}
		vectorDictTemp = {}
		vectorDictTemp['Year'] = []
		vectorDictTemp['Month'] = []
		vectorDictTemp['Day'] = []
		vectorDictTemp['Station'] =[]
		vectorDictTemp['River'] = []
		
		count = 0
		
		if self.selectParm == None:
			#if no stations are selected, pick the top 5 by default
			self.selectTopParm(5)
		
		if self.selectYear == []:
			self.selectYears()
			
		for j in self.stationDict:
			count = 0 #counts the number of sampling dates at each site
			
			for i in self.selectParm:

				if i in self.stationDict[j].setOfParms():
					
					#add the sampling date information only once - for the first selected parm
					#(after data was reorganized, nulls are in place of any missing parameters.
					#thus, position in dataCols matches to correspondding date for each parameter
					
					if i == self.selectParm[0]:
						for k in self.stationDict[j].dataCols[i]:
							if k[0] != None and int(k[0][0:4]) in self.selectYear:
								vectorDictTemp['Year'].append(str(k[0][0:4]))
								vectorDictTemp['Month'].append(str(k[0][5:7]))
								vectorDictTemp['Day'].append(str(k[0][8:10]))
							else:
								vectorDictTemp['Year'].append(robjects.NA_Character)
								vectorDictTemp['Month'].append(robjects.NA_Character)
								vectorDictTemp['Day'].append(robjects.NA_Character)
							
							if k[5] != None and int(k[0][0:4]) in self.selectYear:
								vectorDictTemp['Station'].append(k[5])
							else:
								vectorDictTemp['Station'].append(robjects.NA_Character)
							
							count += 1 
							vectorDictTemp['River'].append(self.stationDict[j].name)
							
					for k in self.stationDict[j].dataCols[i]:
						if k[2] != None and int(k[0][0:4]) in self.selectYear:
							if i in vectorDictTemp:
								vectorDictTemp[i].append(k[2])
							else:
								vectorDictTemp[i] = [k[2]]
							
						else:
							vectorDictTemp[i].append(robjects.NA_Real)

				if i not in vectorDictTemp:
					vectorDictTemp[i]=[]
					
			#before moving to next site, fill a parameter colum with null values 
			#if that parameter has not been sampled at the current site				
			
			for i in self.selectParm:
				if i not in self.stationDict[j].setOfParms():
					for k in range(count):		
						vectorDictTemp[i].append(robjects.NA_Real)
				
						
		#build the R vector colums after all station data collected
		vectorDict['Year'] = robjects.StrVector(vectorDictTemp['Year'])
		vectorDict['Month'] = robjects.StrVector(vectorDictTemp['Month'])
		vectorDict['Season'] = robjects.StrVector(self.toSeason(vectorDictTemp['Month']))
		vectorDict['Day'] = robjects.StrVector(vectorDictTemp['Day'])
		vectorDict['River'] = robjects.StrVector(vectorDictTemp['River'])
			
		for i in self.selectParm:
			vectorDict[i] = robjects.FloatVector(vectorDictTemp[i])
		
		return robjects.DataFrame(vectorDict)


	#produce bar graph from top or selected parameters
	
	def topBarPlot(self,n,filename):
		topParmDict = self.topParm(n)
		vectorDict = {}
		vectorDict['Parameter'] = robjects.StrVector(topParmDict.keys())
		vectorDict['Count'] = robjects.IntVector(topParmDict.values())

		self.barPlot(robjects.DataFrame(vectorDict), filename, "Parameter","Count")
		
	
	def selectBarPlot(self,filename):
		selectedParmDict = {}
		vectorDict = {}
		allParm = self.countAllParm()
		
		if self.selectParm != None:
			for i in self.selectParm:
				selectedParmDict[i] = allParm[i]
					
		vectorDict['Parameter'] = robjects.StrVector(selectedParmDict.keys())
		vectorDict['Count'] = robjects.IntVector(selectedParmDict.values())
		
		newFilename = filename + "_bar_all" 
		self.barPlot(robjects.DataFrame(vectorDict), newFilename, "Parameter", "Count")	
	
	
	def selectRiverBarPlots(self,filename):
		riverDict = {}
		vectorDict = {}
				
		if self.selectParm != None:
			for i in self.selectParm:
				
				riverDict = self.countAllRiverParm(i)
				
				vectorDict['River'] = robjects.StrVector(riverDict.keys())
				vectorDict['Count'] = robjects.IntVector(riverDict.values())
				
				newFilename = filename + "_" +i+"_bar_river"	
				self.barPlot(robjects.DataFrame(vectorDict), newFilename, "River", "Count")
		
		
	#do a boxplot on month or year (mory): month ("Month") or year ("Year")
	def selectBoxPlots(self, filename, mory):
		if self.selectParm == None:
			#if no stations are selected, pick the top 5 by default
			self.selectTopParm(6)
		
		for i in self.selectParm:
			newFilename = filename + "_" + i + "_box_" + mory
			self.boxPlot(self.getSelectParmData(), newFilename, mory, i)
			
			
	
	def selectHistograms(self, filename):
		parmcount = self.countSelectParm()
		if self.selectParm == None:
			#if no stations are selected, pick the top 5 by default
			self.selectTopParm(5)
				
		for i in self.selectParm:
			#check that there are some observations before generating the histogram	
			if parmcount[i] > 0:
				newFilename = filename + "_" + i + "_histogram"
			
				self.histogram(self.getSelectParmData(), newFilename, i, "Season", self.getUnits(i))
	
	def selectScatter(self,filename):
		dataframe = self.getSelectParmData()
		parmcount = self.countSelectParm()
		cols = dataframe.names
		#determine whether plot scale should be log transformed
		logx = False
		logy = False
		if len(self.selectParm) >= 2:
			#only produce a plot when there are two or more selected parameters
			#produce a plot of 			
			for i in range(len(self.selectParm)):
				for j in self.selectParm[i+1:]:
					if i != j:
						parm1 = self.selectParm[i]
						parm2 = j
						
						#check that selected paramters have at least one observation
						if parmcount[parm1] > 0 and parmcount[parm2] > 0:
						
							units1 = self.getUnits(parm1)
							units2 = self.getUnits(parm2)
						
							if abs(self.skewness(dataframe[cols.index(parm1)])) > 1:
								logx = True
							if abs(self.skewness(dataframe[cols.index(parm2)])) > 1:
								logy = True
						
							newFilename = filename + "_" + parm1 + "_" + parm2
							self.scatter(dataframe,newFilename,parm1,parm2,\
								units1,units2,"Season",logx,logy)
					
					
				
			
		
		
	#called only by graphing methods 					
	def barPlot(self, dataframe, filename, x_parm, y_parm): 
		
		grdevices.png(file=filename, width=512, height=512)
		data = ggplot2.ggplot(dataframe)
		aes = ggplot2.aes_string(x=x_parm,y=y_parm)
		geom = ggplot2.geom_bar(stat = "identity")
		gg = data + aes + geom
		gg.plot()
		grdevices.dev_off()
		
	def boxPlot(self, dataframe, filename, x_parm, y_parm): 

		grdevices.png(file=filename, width=512, height=512)
		data = ggplot2.ggplot(dataframe)
		aes = ggplot2.aes_string(x=x_parm,y=y_parm,)
		geom = ggplot2.geom_boxplot(alpha = 0.7,fill="aquamarine3")
		gg = data + aes + geom
		gg.plot()
		grdevices.dev_off()
		
	def histogram(self, dataframe, filename, parm, group, units):
		with suppress_stdout():
			grdevices.png(file=filename, width=512, height=512)
			data = ggplot2.ggplot(dataframe)
			aes = ggplot2.aes_string(x=parm,fill = group)
			geom = ggplot2.geom_histogram(colour="black")
			labs = ggplot2.labs(x=parm + " " + units)
			gg = data + aes + geom + labs
			gg.plot()
			grdevices.dev_off()
	
	def scatter(self, dataframe, filename, parm1, parm2, units1, units2, group,logx,logy):
		grdevices.png(file=filename, width=512, height=512)
		data = ggplot2.ggplot(dataframe)
		aes = ggplot2.aes_string(x=parm1, y=parm2,colour=group)
		geom = ggplot2.geom_point(alpha = 0.7)
		labs = ggplot2.labs(x=parm1+ " " + units1, y=parm2 + " " + units2)
		xlogscale = ggplot2.scale_x_log10()
		ylogscale = ggplot2.scale_y_log10()
		
		if logx == True and logy == True:
			gg = data + aes + geom + labs + xlogscale + ylogscale
		elif logx == True:
			gg = data + aes + geom + labs + xlogscale 
		elif logy == True:
			gg = data + aes + geom + labs + ylogscale
		else:
			gg = data + aes + geom + labs 
			
		gg.plot()
		grdevices.dev_off()
	
	#export currently selected sites and parameters to a csv file. 
		
	def export(self,filename):
		if self.numOfStations() < 1000:
			data = self.getSelectParmData()
			data.to_csvfile(filename)	
			
	def exportSummary(self, log, filename):
		parmSum = self.summary()
		sites = self.numOfStations()
		
		#export selection stations and rivers
		f = open(filename,'w')
		f.write("Summary data on selected stations and paramters.\n\n")
		#export the log data:
		f.write("\nSelection log:\n")
		for i in log:
			f.write(i+"\n")
		
		f.write("\nCurrent selection has " + str(sites) + " stations.\n\n")
		
	
		
		f.write("\nValue summary:\nParameter,n,Mean,Median,Standard Deviation\n")

		parmSum = self.summary()
		for j in parmSum: 
			f.write(j+",")
			for i in parmSum[j]:
				f.write(str(i)+",")
			f.write("\n")
			
			
		if len(parmSum) > 1:
			f.write("\nPearson's correlation\nParamter,Correlation coeeficient,P-value\n")
			for j in parmSum:
				for k in parmSum:
					if k != j:
						cor = self.pearsons(j,k) #returns a tupple; correlation coef and p-value
						f.write(j +" vs " + k + " :" + str(round(cor[0],4))\
							+ "," + str(round(cor[1],4))+"\n")
						
		f.write("\n\nList of rivers with observation for selected parameters:")
		for j in parmSum:
			f.write("\n" + j+" ("+self.getUnits(j)+")\n")
			rivers= self.countAllRiverParm(j)
			for i in rivers:
				f.write(i + "," + str(rivers[i]) + "\n")
		f.close()
		
					
			
	

