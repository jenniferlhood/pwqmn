from pwqmn_data import station, allStationData
import UI

class program():

	def __init__(self):
	
		#two main data objects: all data and selected data
		self.allData = None
		self.selectedData = None
		self.msgList = []
		self.selectionLog = []
		
	def loadFiles(self):
	
		#load all data from .csv files specified in config
		config = open('config.txt').read().split("\n")
		cities = ""
		sites = ""
		dataList = []
	
		noCitiesFlag = True
		noSitesFlag = True
		noDataFlag = True
	
	
		for i in config:
			line = i.split(":") 
			
			if len(line) == 2:
				if line[0] == 'cities':
					cities =	line[1]
					noCitiesFlag = False
				elif line[0] == 'sites':
					sites = line[1]
					noSitesFlag = False
				else:
					dataList.append(line[1])
					noDataFlag = False

		if noSitesFlag == noDataFlag == False:
			#add the site data
			self.allData = allStationData(sites)
			self.msgList.append("Site data loaded.")
			
			##add all the data to each site
			for i in dataList:
				self.allData.getStationData(i)
				self.msgList.append("Data from "+i+" loaded.")
			##Reorganize data
			self.allData.allReorganize()
		
		else:
			if noSitesFlag == True:	
				self.msgList.append("No Site data found,check config.txt or file location.")
			if noDataFlag == True:	
				self.msgList.append("No water quality data found, check config.txt or file location.")
		
		if noCitiesFlag == False:
			self.allData.getCities(cities)
			self.msgList.append("Cities loaded.")
		else:
			self.msgList.append("No cities found, check config.txt or file location.")
	
	""" ------------------------------------------------------------
	The list command. 
	Use to see which sites, parameters, years and cities are avaialble
	in the data set, and which of these is present in the current selection
	 ------------------------------------------------------------"""
	
	def ls(self,parms):
		lsDict = {}
		self.msgList = []
		
		if parms == None:
			lsDict = None
	
		elif parms[0:3] == "-as":

			lsDict = self.allData.setOfStations() 
			#add header entry to provide information on what is in the dict
			lsDict["Head"] = "station"
		
		elif parms[0:3] == "-ss":

			if self.selectedData != None:
				lsDict = self.selectedData.setOfStations() 
				lsDict["Head"] = "station"
			else:
				lsDict["Head"] = "No stations currently selected. Use sel to make selection"
			
		elif parms[0:3] == "-ap":

			lsDict = self.allData.countAllParm()
			lsDict["Head"] = "parm"
		
		elif parms[0:3] == "-sp":

			if self.allData.selectParm != []:
			
				#if there are stations selected, display the counts for the selected stations
				# otherwise, display counts for all data available
				if self.selectedData != None:
					lsDict = self.selectedData.countSelectParm()
					lsDict["Head"] = "parm"
					self.msgList.append("*Counts on currently selected stations")
				else:
				
					lsDict= self.allData.countSelectParm()
					lsDict["Head"] = "parm"
					self.msgList.append("*Counts on all available data (no stations selected)")
					
			else:
				lsDict["Head"] = "No parameters currently selected. Use sparm to make selection"
			
		elif parms[0:3] == "-ar":

			lsDict = self.allData.countAllRivers()
			lsDict["Head"] = "river"

		elif parms[0:3] == "-sr":

			if self.selectedData != None:	
				lsDict = self.selectedData.countAllRivers()
				lsDict["Head"] = "river"
			else:
				lsDict["Head"] = "No stations currently selected. Use sel to make selection"
				
		elif parms[0:3] == "-ac":

			cities = self.allData.cityDict.keys()
			for i in cities:
				lsDict[i] = ""
			lsDict["Head"] = "city"

		else:
			lsDict["Head"] = "That list option does not exist."
	
		UI.ls(lsDict)
		UI.messages(self.msgList)
		


	""" ------------------------------------------------------------
	The select stations command. 
	Used to make a subset of data on which to generate stats and graphs
	 ------------------------------------------------------------"""
	def sel(self,parms):
		riverCount = {}
		
		if parms == None:
			UI.sel(None)
			
		elif parms[0:4] == "-all":
			pass
			
		elif parms[0:6] == "-river":
		
			if len(parms) > 7:
				river = parms[7:]
				
				#check if the river is valid
				if river in self.allData.countAllRivers():
				
					#create the selection
					self.selectedData = self.allData.selectRiver(river)
					self.selectionLog = [parms] #log the selection
					
					riverCount = self.selectedData.countAllRivers()
					self.msgList.append(river + " selected. "+ str(riverCount[river])\
						+ " stations added to selection.")
					

				else:
					self.msgList.append("No data for specified river found.")			
			else:
				self.msgList.append("No river specified.")
						
		elif parms[0:4] == "-add":
		
			if len(parms) > 5:
				river = parms[5:]
				
				if river in self.allData.countAllRivers():
					#if there is no current selection, the append function will generate the selection
					if self.selectedData == None:
						
						#create the selection
						self.selectedData = self.allData.selectRiver(river)
						self.selectionLog = [parms] #log the selection
						
						
						riverCount = self.selectedData.countAllRivers()
						self.msgList.append(river + " selected. "+ str(riverCount[river])\
						+ " stations added to selection.")
						#self.ls("-sr")
						#check that the river is valid and data has been generated for selectData

					else:
						#append function called on all data (which is the source of the new
						# data to append to the selected data)
						self.allData.addRiver(self.selectedData,river)
						self.selectionLog.append(parms) #log the selection
						
						riverCount = self.selectedData.countAllRivers()
						self.msgList.append(river + "added. "+ str(riverCount[river])\
						+ " stations added to selection.")
					

				else:
					self.msgList.append("No data for specified river found.")			
			else:	
				self.msgList.append("No river specified.")
				
		elif parms[0:4] == "-rem":
			if len(parms) > 5:
				river = parms[5:]
				if river in self.selectedData.countAllRivers():
					self.allData.removeRiver(self.selectedData,river)
					self.selectionLog.append(parms) #log the selection
					
					self.msgList.append(river + " removed from selection")
										
					#check that there are sites remainin in selection
					# empty selection if not
					if self.selectedData.numOfStations() == 0:
						self.selectedData = None

				else:
					self.msgList.append("River not in selected data.")
			else:	
				self.msgList.append("No river specified.")
				
		elif parms[0:5] == "-city":
			if len(parms) > 6:
				
				#parse the input
				city = filter(str.isalpha,parms[6:])
				kms = filter(str.isdigit,parms[6:])
				
				if city != "" and kms != "":
				
					#check that the city is valid
					if city in self.allData.cityDict:
						
						#create the selection
						self.selectedData = self.allData.selectCity(city, int(kms))
						self.selectionLog = [parms] #log the selection
						
						#if no stations found by the select city function, 
						# set the selection back to none
						if self.selectedData.stationDict == {}:
							self.msgList.append("No stations found within " + kms + " km of " + city)
							self.selectedData = None
						else:
							self.msgList.append("Selected all sites within " + kms + " km of " + city)
												
					else:
						self.msgList.append("City not available")
						self.msgList.append("Check avaialble cities (ls) or add to list.")
				elif kms == "":
					self.msgList.append("Please specify distance (in km).")
				else:
					self.msgList.append("Please enter a city name. Check the list of cities (ls).")	
			else:	
				self.msgList.append("No city specified.")		
					
		else:
			self.msgList.append("That selection option does not exist.")
		
		if self.selectedData != None:
			self.msgList.append("The following rivers are in the current selection:")
		
					
		UI.sel(self.msgList)
		self.ls("-sr")
		self.msgList = []
		
	
	
	
	""" ------------------------------------------------------------
	The select parameters command. 
	Used to select parameters on which to produce stats and graphs
	 ------------------------------------------------------------"""	
		
	def sparm(self,parms):
		self.msgList = []
		
		if parms == None:
			UI.sparm(None)

		elif parms[0:4] == "-top":
			if len(parms) > 4:
				num = int(filter(str.isdigit,parms[5:]))
				self.msgList.append("Top " + str(num) + " parameters were selected.")
			else:
				num = 5
				self.msgList.append("Number of paramters to select not specified.")
				self.msgList.append("Top 5 parameters were selected.")
				
			self.allData.selectTopParm(num)
			if self.selectedData != None:
				self.selectedData.selectTopParm(num)
			
			
				
		elif parms[0:4] == "-add":
			if len(parms) > 4:
				parameter = parms[5:]
				
				#check that the paramter is valid
				if parameter in self.allData.setOfParms():
					if parameter in self.allData.selectParm:
						self.msgList.append("Parameter already selected.")
					else:
						self.allData.addParm(parameter)
						if self.selectedData != None:
							self.selectedData.addParm(parameter)
							
						self.msgList.append(parameter + " added to selection.")
						
				else:
					self.msgList.append(parameter + " not found.")
			else:
				self.msgList.append("No parameter to add.")
			
				
		elif parms[0:4] == "-rem":
			if len(parms) > 4:
				parameter = parms[5:]
				
				#check that the parameter is valid
				if parameter in self.allData.selectParm:
					self.allData.removeParm(parameter)
					if self.selectedData != None:
						self.selectedData.removeParm(parameter)
					self.msgList.append(parameter + " removed.")
				else:
					self.msgList.append(parameter + " not in selection.")
			else:
				self.msgList.append("No parameter to remove.")
		else:
			self.msgList.append("That selection option does not exist")
			
		if self.allData.selectParm != []:
			self.msgList.append("The following parameters are currently selected:")
		
		UI.sparm(self.msgList)
		self.ls("-sp")
		
	
	""" ------------------------------------------------------------
	The stat command. 
	Generates summary statistics for selected stations and parameters
	 ------------------------------------------------------------------"""		
			
	def stat(self,parms):
		print parms
		self.msgList = []
		
		if parms == None:
			UI.stat(None)
		else:
			if self.selectedData != None and self.allData.selectParm != []:
				if parms[0:2] == "-s":
					if len(parms) <= 3:
						self.msgList.append("Need to provide filename.")
					else:
						filename = parms[3:]
						self.selectedData.exportSummary(self.selectionLog,filename)
						self.msgList.append("Summary exported.")
				else:
					self.msgList.append("That option does not exist")
			else:
				if self.selectedData == None:
					self.msgList.append("No stations currently selected.")
				if self.allData.selectParm == []:
					self.msgList.append("No parameters currently selected.")
			
			UI.stat(self.msgList)
			
	""" -----------------------------------------------------------------
	The graph. 
	uses R ggplot to generate graphs on selected stations and parameters
	 --------------------------------------------------------------------"""	
		
	def graph(self,parms):
		if parms == None:
			UI.graph(None)

		else:
			if self.selectedData == None:
				self.msgList.append("No stations currently selected")
			if self.allData.selectParm == []:
				self.msgList.append("No parameters currently selected")
				
			if self.selectedData != None and self.allData.selectParm != []:	
			
				parms = parms.split(" ")
		
				
				if len(parms) == 2:
					filename = parms[1]
					if parms[0] == "-scatter":
						if len(self.allData.selectParm) > 1:
							self.selectedData.selectScatter(filename)
							self.msgList.append("Scatter plots generated.")
						else:
							self.msgList.append("Must have at least two selected paramters.")
					elif parms[0] == "-hist":
						self.selectedData.selectHistograms(filename)
						self.msgList.append("Histogram generated.")
					elif parms[0] == "-bar" or parms[0] == "-box":
						self.msgList.append("Need to provide filename")	
					else:
						self.msgList.append("That graph option does not exist.")	
				elif len(parms) == 3:
					filename = parms[2]
				
					if parms[0] == "-bar":
						if parms[1] == "all":
							self.selectedData.selectBarPlot(filename)
							self.msgList.append("Bar plots generated.")
						elif parms[1] == "river":
							self.selectedData.selectRiverBarPlots(filename)
							self.msgList.append("Bar plots generated.")
						else:
							self.msgList.append("That graph option does not exist.")
					elif parms[0] == "-box":
						if parms[1] == "m":
							self.selectedData.selectBoxPlots(filename,"Month")
							self.msgList.append("Box plots generated.")
							
						elif parms[1] == "y":
							self.selectedData.selectBoxPlots(filename,"Year")
							self.msgList.append("Box plots generated.")
						elif parms[1] == "r":
							self.selectedData.selectBoxPlots(filename,"River")
							self.msgList.append("Box plots generated.")
					else:
						self.msgList.append("That graph option does not exist.")
				
				else:
					self.msgList.append("That graph option does not exist.")
				
		UI.messages(self.msgList)
		self.msgList = []	
	"""
	======================================================
				Main program loop
	======================================================
	"""	
	def run(self):
		UI.welcome()
		
		self.loadFiles()
		
		UI.messages(self.msgList)
		quit = False
	
		#If any of the files did not load, program quits
		if self.allData == None:
			quit = True

		
		while quit == False:
			line = raw_input("~~> ")
			self.msgList=[]
			
			if line == "":
				pass
			elif line == "cmd" or line == "c" or line == "h" or line == "help":
				UI.cmds()
		
			elif line[0:2] == "ls":
				if len(line) > 3:
					self.ls(line[3:])
				else:
					self.ls(None)
					
			elif line[0:3] == "sel":
				if len(line) > 4:	
					self.sel(line[4:])
				else:
					self.sel(None)

			elif line[0:5] == "sparm":
				if len(line) > 6:			
					self.sparm(line[6:])
				else:
					self.sparm(None)

			elif line[0:4] == "stat":
				if len(line) > 5:
					self.stat(line[5:])		
				else:
					self.stat(None)

			elif line.find("graph") != -1:
				if len(line) > 6:
					self.graph(line[6:])
				else:
					self.graph(None)	
			elif line[0] == "q":
				quit = True
			else:
				self.msgList.append("command not found")
				UI.messages([])
				
			
			
