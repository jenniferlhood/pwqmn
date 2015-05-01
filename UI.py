#provides messages to user, checks that proper input has been provided for each command
def messages(msgList):
	for i in msgList:
		print i
	print ""
		
def welcome():
	print ""
	print "===================================================================="
	print " Welcome to the PWQMN data utility. Enter cmd for list of commands."
	print "===================================================================="
	print ""
	
def cmds():
	ls(None)
	sel(None)
	sparm(None)
	stat(None)
	graph(None)
	
def ls(parm): #parameter will be a dict
	print ""
	if parm == None:
		print "---------------------------------------------------------"
		print "ls"
		print "Use: list some aspects of the dataset"
		print "     the following options are available:"
		print ""
		print "   -as \t\t to list all available stations"
		print "   -ss \t\t to list selected stations"
		print "   -ap \t\t to list all available parameters"
		print "   -sp \t\t to list the selected parameters"
		print "   -ar \t\t to list all rivers"
		print "   -sr \t\t to list rivers of selected stations"
		print "   -ac \t\t to list all available cities"
		print ""	
		
	else:
		if parm == {}:
			print "command not found"
		if parm["Head"] == "station":
			del parm["Head"]
			print "Station \t\t River name"
			print "------------------------------------------"
			for i in parm:
				print i, "\t\t", parm[i]
			
		elif parm["Head"] == "parm":
			del parm["Head"]
			print "Parameter \t Number of Observations"
			print "------------------------------------------"
			for i in parm:
				print i, "\t\t\t", parm[i]
				
		elif parm["Head"] == "river":
			del parm["Head"]
			print "Number of stations \t River name"
			print "------------------------------------------"
			for i in parm:
				print "\t", parm[i], "\t\t",i
					
		elif parm["Head"] == "city":
			del parm["Head"]
			print "Included cities"
			print "------------------------"
			for i in parm:
				print i
				
		else:
			print parm["Head"]
				
		
def sel(parm): #parameter will be a list
	if parm == None:
		print "---------------------------------------------------------"
		print "sel"
		print "Use: The select command. Select a subset of stations"
		print "     from among all availbale stations. Stats and graphs are"
		print "     produced on selected sites."
		print ""
		print "   -river <river> \t select by river"
		print "   -add <river> \t append river selection"
		print "   -rem <river> \t remove river from  selection"
		print "   -rem zero \t\t remove stations with zero observations"
		print "   -rem x \t\t remove stations with less than x observations" 
		print "   -city <city> <x> \t all sites x kms from city"
		print ""
	else:
		messages(parm)

			
def sparm(parm):
	if parm == None:
		print "---------------------------------------------------------"
		print "sparm"
		print "Use: The select parameters command. Select a subset of"
		print "     parameters from among all available parameters. Stats"
		print "     and graphs are produced on selected parameters."
		print "	  the following options are available: "
		print ""
		print "   -top x \t\t top x most observed parameters"
		print "   -add <param> \t add parameter to selected"
		print "   -add <year> \t\t add year to selected years"
		print "   -rem <param> \t remove parameter from selected"
		print "   -rem <year> \t\t remove year from selected years"
		print ""
	else:
		messages(parm)
		
		
def stat(parm):
	if parm == None:
		print "---------------------------------------------------------"
		print "stat"
		print "Use: produce basic statistics on selected sites and parameters"
		print ""
		print "   -s <filename> \t produce summary output on selected"
		print ""
	else:
		messages(parm)
	
def graph(parm):
	if parm == None:
		print "---------------------------------------------------------"
		print "graph"
		print "Use: produce graphs on selected sites and parameters"
		print ""
		print "   -bar all <filename> \t\t bar plot of number of observations"
		print "   -bar river <filename> \t bar plots by river"
		print "   -hist <filename> \t\t histograms for selected parameters"
		print "   -box m <filename>  \t\t box plots by month"
		print "   -box y <filename>  \t\t box plots by year"
		print "   -box r <filename>  \t\t box plots by river (all dates)"
		print "   -scatter <filename> \t\t scatter plots for parameters"
		print ""
	else:
		messages(parm)
