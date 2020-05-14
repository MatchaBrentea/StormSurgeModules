import sys
import datetime
import shapefile
import numpy as np
import matplotlib.path as mpltPath
from scipy.spatial import distance
from geopy.distance import distance as gdist
from adpy import*




class Warnings:
	"""
	Responsible for creating storm surge warnings and notification up to the town level of a given province.

	"""

	def __init__(self,shape_file,shape2_file,shape3_file,filt,fort_14,fort_15,maxelev63,fort_63,radiusOffset,neighborFilesDir):
		"""
		Warnings Initialization.
		Initialized given arguments and performs preliminary procedures before warning generations.

		Parameters
		----------
		shape_file : .shp file
			.shp file for towns/municipalities/cities.
		shape2_file : .shp file
			.shp file for barangays.
		shape3_file : .shp file
			.shp file for provinces.
		filt : string
			scope of warnings(province level)
		fort_14 : fort.14 file
			This file includes topography/bathymetry of a bounded area. 
			It also includes the meshes and boundaries needed for the warning generations.
		fort_15 : fort.15 file
			model parameter and boundary information file
		maxelev63: maxele.63 file
			This file describes provides the maximum elevations at a particular node in the mesh provided by fort_14
		fort_63 : fort.63 file
			This include time-series information on the nodes.
		radiusOffset : integet/float
			(not needed for now)
		neighborFilesDir : string(directory path)
			This path is needed the .neighbors file to be used for town notifications.
			.neighbor files are files that provides the neighbors of a town in  a particular province(filt)
		"""


		self.shape_file=shape_file
		self.shape2_file=shape2_file
		self.shape3_file=shape3_file
		self.filt=filt
		self.fort_14=fort_14
		self.fort_15=fort_15
		self.maxelev63=maxelev63
		self.fort_63=fort_63
		self.radiusOffset=radiusOffset
		self.neighborFilesDir=neighborFilesDir

		print("parsing files",datetime.datetime.now())
		self.sf =  shapefile.Reader(self.shape_file)
		self.sf2 =  shapefile.Reader(self.shape2_file)
		self.sf3 =  shapefile.Reader(self.shape3_file)
		self.AGRID,self.NE,self.NP,self.X,self.Y,self.DP,self.NM = read_fort14(self.fort_14)
		self.RUNDES,self.RUNID,self.AGRID,self.NDSETSE,self.ETA = read_maxelev63(self.maxelev63)

		#list that will contain warnings and notifications and early surges
		self.warnings=[]
		self.notifications=[]
		self.earliestSurges=[]


	def __str__(self):
		return "Warnings and notifications for " + self.filt + "\n"

	
	def getCenter(self,arr):
		"""
		Gets the center of a list of points.

		Parameters
		----------
		arr : list
			list of points

		Returns
		-------
			2-tuple
				returns the center of all points in arr
		"""

		return (sum([i[0] for i in arr])/len(arr),sum([i[1] for i in arr])/len(arr))

	def findMaxDist(self,a,arr):
		"""
		Gets the distance of the farthest point from the center of a list of points.
		findMaxDist helps in optimizing the search process in determining the points that are inside a polygon.

		Parameters
		----------
		a : 2-tuple
			center of all the points in arr
		arr: list
			list of points
	
		Returns
		-------
			float
				returns the distance of the farthest point included in arr relative to a
		"""
		return max([gdist(a,i).meters for i in arr])	

	'''def getDirection(self,pointA,pointB):
		#gets the direction of pointB relative to point A
		#not sure if this function is still needed
		if pointB[0] - pointA[0] > 0 :
			if(pointB[1] - pointA[1]) == 0 :
				return "E"
			elif(pointB[1] - pointA[1]) > 0 :
				return "NE"
			else:
				return "SE"
		elif pointB[0] - pointA[0] < 0 :
			if(pointB[1] - pointA[1]) == 0 :
				return "W"
			elif(pointB[1] - pointA[1]) > 0 :
				return "NW"
			else:
				return "SW"
		else:
			if(pointB[1] - pointA[1]) > 0 :
				return "N"
			else:
				return "S"			
	'''
	def extractFieldNames(self,sf):
		"""
		Gets the attributes of self.shape_file

		Parameters
		----------
			sf : shapefile.Reader instance
				shapefile parser	
		Returns
		-------
			list
				returns the list of attributes of self.shape_file
		"""	

		fields = sf.fields[1:] 
		field_names = [field[0] for field in fields]
		return field_names

	def findCandidatePoints(self,center,maxDist,candidatePoints,candidatePoints_index):
		"""
		Finds all the points that is within a specific range relative to a certain point.
		It measures all the distances of each the points in self.fort_14 and appended it to a list.
		if its less than or equal to a certain distance. Index of appeded points is also appended to another list.
		This function filters all the points that could be included in the generation of warnings and thus minimized
		the search area later on for determining if certain points are inside a polygon.

		Parameters
		----------
		center : 2-tuple
			the reference point in which to measure the distance to all the points in (self.X,self.Y)
		maxDist : float
			the maximum distance from a point in self.X,self.Y to center to be included in candidatePoints
		candidatePoints: list
			stores all the included points
		candidatePoints_index : list
			stores all the indexes of all the included points in candidatePoints
	
		Returns
		-------
			(results are returned in candidatePoints and candidatePoints_index)
		"""
		for i in range(1,len(self.X)):
			if gdist(center,(self.X[i],self.Y[i])).meters < maxDist + self.radiusOffset:
				if(self.ETA[i]) != -99999:
					candidatePoints.append((self.X[i],self.Y[i]))
					candidatePoints_index.append(i)		

	def updateWarnings(self,pointIndexInsideGeom,town_name):

		"""
		Adds a town,its maximum predicted water elevation measure and its barangay of origin to self.warnings.
		Given all the points inside a given town, it finds the maximum water elevation measure among this points.
		It gets the coordinate of the founded maximum water elevation measure. All points inside a given town are then 
		removed from self.X,self.Y (to minimized search areas for next iterations). WIth the founded coordinates,
		it will find which barangay the coordinates are in. The town name , the maximum water elevation measure and
		its barangay of origin are now then included in the list of warnings.

		Parameters
		----------
		pointIndexInsideGeom : list
			Index of all the points included in the polygon of town_name
		town_name : string
			name of the iven town
	
		Returns
		-------
		"""

		maxElev=max([self.ETA[i] for i in pointIndexInsideGeom])
		maxElevIndex=self.ETA.index(maxElev)
		xCoordOfMaxElev=self.X[maxElevIndex]
		yCoordOfMaxElev=self.Y[maxElevIndex]


		for i in pointIndexInsideGeom:
			self.X[i]=self.Y[i]=self.ETA[i]="rem"
		self.X=list(filter(lambda a: a != "rem", self.X))
		self.Y=list(filter(lambda a: a != "rem", self.Y))
		self.ETA=list(filter(lambda a: a != "rem", self.ETA))
		barangayOfHighestSurge=self.getBarangayOfHighestSurge(town_name,xCoordOfMaxElev,yCoordOfMaxElev)
		self.warnings.append((town_name,maxElev,barangayOfHighestSurge))
		#print(barangay_name,maxElev)

	def updateNotifications(self):
		"""
		Finds all the neighbors of all the towns with storm surge warnings within a given province.
		First it will find if there is .neighbor file for the given province.
		If none, it will create .neighbor file for that province. 
		Creation of .neigbor file is as follow:
			For two town;town A and town B, if there exist a point from its polygons that are the same, 
			then townA is a neighbor of townB.
		This neighbor file will be use to determine which are towns are beside a town with storm-surge warnings.
		*add more documentation, this is still not complete

		Parameters
		----------

		Returns
		-------

		"""

		try:
			f=open(self.neighborFilesDir+self.filt+".neighbors","r")
		except FileNotFoundError:
			print("file not found, creating new neighbor file for",self.filt)
			self.createNeighborFile()
			f=open(self.neighborFilesDir+self.filt+".neighbors","r")

		affectedAreas=set([i[0] for i  in self.warnings])

		for line in f.readlines():
			#print(line)
			townNeighbors=line[:-1].split(",")
			town=townNeighbors.pop(0)
			Neighbors=set(townNeighbors)
			if town in affectedAreas:
				print("Affected neightbors of",town)
				diff = Neighbors.difference(affectedAreas)
				print(diff)
				self.notifications.append((town,diff))

		#do we still have to notify warned areas kung ano yung nareport sa neighbors nila? tanungin natin si maam sa monday

	def createNeighborFile(self):		
		"""
		Create a neighbor file for a given province.
			For two town;town A and town B, if there exist a point from its polygons that are the same, 
			then townA is a neighbor of townB.
		Neighbor are in the format:
			<Town> [Neighboring Towns]*
			....
			....
			....
		This neighbor file will be use to determine which are towns are beside a town with storm-surge warnings.

		Parameters
		----------

		Returns
		-------
		"""

		Province=self.filt
		f=open(self.neighborFilesDir+Province+".neighbors",'w')


		fields=self.sf.fields[1:]
		field_names = [field[0] for field in fields]
		for r in self.sf.shapeRecords():
			x=x+1
			atr=dict(zip(field_names,r.record))
			if(atr['NAME_1'] == Province):
				geom = r.shape.points
				#parts = r.shape.parts
				town = r.record[6]
				set_geom = set(geom)
				f.write(town)

				for s in self.sf.shapeRecords():
					atr2=dict(zip(field_names,s.record))
					if(atr2['NAME_1'] == Province):
						geom2 = s.shape.points
						#parts = r.shape.parts
						town2 = s.record[6]
						set_geom2 = set(geom2)

						#print(set_geom.intersection(set_geom2))
						if set_geom.intersection(set_geom2) != set() and town!=town2:
							#print(","+town2)
							f.write(","+town2)

				f.write("\n")
		f.close()

	def filterNodes(self,parts,geom,candidatePoints,paths,insides):
		"""
		Finds all the points in a given list of points that are inside a polygon.
		For all closed paths. Filter all the points in candidatePoints that are inside that closed paths.
		
		Parameters
		----------
		parts : list
			list of all the closing points of a polygon. It is possible that an administrative boundary can have more than one shapes.
		geom : list
			list of points that bounds a specific town.
		candidatePoints : list
			list of all points to be checked if its inside or part of a town.
		paths : list
			list of all the paths that defines a polygon
		insides : list
			list of boolean values reflected from candidatePoints. If the value of insides[i] is True then the point candidatePoints[i] is included in a certain polygon.
		
		Returns
		-------

		"""
		for i in range(0,len(parts)):
			if(i < len(parts) - 1):
				path = mpltPath.Path(geom[parts[i]:parts[i+1]])		
				inside=path.contains_points(candidatePoints)
				paths.append(path)
				insides.append(inside)
			else:
				path = mpltPath.Path(geom[parts[i]:len(geom)])		
				inside=path.contains_points(candidatePoints)				
				paths.append(path)
				insides.append(inside)

	def getBarangayOfHighestSurge(self,townFilter,xCoordOfMaxElev,yCoordOfMaxElev):
		"""Finds the location of the highest surge in specific town.

		Parameters
		----------
		parts : list
			list of index of points that divides a certain geometry.(Shapes in a certain town can have multiple Geometries/Polygons)
		townFilter : string
			town/city of interest
		xCoordOfMaxElev : float
			x coordinate of highest surge
		yCoordOfMaxElev : float
			y coordinate of highest surge
		Returns
		-------
			barangay_name : string
				returns the barangay_name of the point (xCoordOfMaxElev.yCoordOfMaxElev) is located. 
		"""

		fields = self.sf.fields[1:] 
		field_names = [field[0] for field in self.sf2.fields[1:]]
		for r in self.sf2.shapeRecords():
			atr = dict(zip(field_names,r.record))
			if atr['NAME_2'] == townFilter: 

				geom = r.shape.points
				parts = r.shape.parts		

				barangay_name = r.record[8]
				paths=[]
				insides=[]

				self.filterNodes(parts,geom,[(xCoordOfMaxElev,yCoordOfMaxElev)],paths,insides)

				compressedInsides=[]

				for inside in insides:
					if(any(inside)):
						compressedInsides.append(True)
					else:
						compressedInsides.append(False)

				if(any(compressedInsides)):
					#print(barangay_name)
					return 	barangay_name

	def getShoreline(self,townGeom):
		"""Finds the shoreline of a specific town. It finds all the list of points in a town's geometry that is beside bodies of water.
		   This would be achieved by getting the intersection of points, between the town and the province.
		   Note : 	This code works for provinces, beside the sea. This assumption would be reasonable because 
		   			of the underlying physics of storm surge.

		Parameters
		----------
		townGeom : list
			list of points that bounds a specific town.
		Returns
		-------
			returns the shoreline of that town. To be specific, the set containing the intersection of thw town and the province geometry. 
		"""

		#gets the points that are include from the shorelines
		field_names = self.extractFieldNames(self.sf3)

		for r in self.sf3.shapeRecords():
			atr = dict(zip(field_names,r.record))
			if atr['NAME_1'] == self.filt: 
				geom = r.shape.points
				parts = r.shape.parts		
				return list(set(geom).intersection(set(townGeom)))

	def updateShorelineWarnings(self,shoreline,candidatePoints,candidatePoints_index):
		"""Finds the best and most accurate predicted water elevation measure within 1 km of a town's  shoreline.
		   It works as follow:
				For each candidate point, if there exist a point in shoreline such that the distance
				between the candidate point and that point is the shoreline is within 1000 meters, 
				append the water eleveation of that candidae point to the list of water elevation near shoreline.
				Find the maximum value of the list and return.

		Parameters
		----------
		shoreline : list
			list of points correspoinding to the shoreline of a specific town.
		candidatePoints : list
			list of points which a specific town that is a potential water elevation near shoreline warning.
		candidatePoints_index: list
			list of integers that will be used to access the water elevation measurement of a certain point in candidatePoints.
		Returns
		-------
			This function returns the maximum elevation in a list of potential water elevation near shoreline warnings.
		"""
		waterElevNearShoreline=[]
		for i in range(1,len(candidatePoints)):
			for j in shoreline:
				if gdist(candidatePoints[i],j).meters < 1000:
					waterElevNearShoreline.append(self.ETA[candidatePoints_index[i]])
					break
		try:
			return max(waterElevNearShoreline)
		except ValueError:
			return

	def generateWarnings(self):
		"""Generates and provides warnings/notifications to affected areas/towns of a certain province.
		   This function consolidates all the warnings,notifications and shoreline warnings and
		   serves as a main umbrella functions for the different methods in this class.
		   The function work as follow:
		   		For each town, it will search for all candidatePoints for warnings,notifications etc. 
		   		If there are candidatePoints, it filters the nodes, and finds if there are points inside 
		   		the towns geometry. If there are points inside geomtry, it updates the warnings and notifications array.
		   		If there are no points inside the town's geomtetry, then it will update warnings for the shoreline.
		   		If there are no candidatePoints, do nothing.


		Parameters
		----------
		Returns
		-------
		"""
		print("generating warning/notifications",datetime.datetime.now())
		field_names = self.extractFieldNames(self.sf)
				
		#	generate warnings for each towns...
		nTowns=0
		nShapes=0
		nPoints=0
		for r in self.sf.shapeRecords():
			#	extract information from .shp file
			atr = dict(zip(field_names,r.record))

			#	filter shape file with command line argument "filt" (provincial filter na to)
			if atr['NAME_1'] == self.filt: 


				geom = r.shape.points
				parts = r.shape.parts		

				nTowns+=1
				nShapes+=(len(parts)-1)
				nPoints+=len(geom)

				#	find the center of the town and the farthest distance of the vertex of the polygon 
				#	describing the town
				town_name = r.record[6]
				print(town_name)
				center=self.getCenter(geom)
				maxDist=self.findMaxDist(center,geom)

				#initialized array for paths,insides,candidatePoints,candidatePoints_index,pointIndexInsideGeom
				paths =[]
				insides=[]
				candidatePoints=[]
				candidatePoints_index=[]
				pointIndexInsideGeom=[]


				'''iterate over all fort.14 nodes and take note of all the nodes
					that have distance from the center of barangay less than or equal to
					the distance of farthest vertex. In this way, you are assured that 
					all the points inside the polygon are in this set of points(candidatePoints).
					This also needed to make the program optimized. Instead of iterating 
					and checking if each fort.14 nodes inside the polygon, you just have to check 
					the set of points that satisfy above conditions.
				'''
				self.findCandidatePoints(center,maxDist,candidatePoints,candidatePoints_index)

				'''		Case 1. There are candidatePoints
							1.1 There are points inside the polygon
								Find the maximum elevation of all the points inside the polygon
								and update Warnings for that town. Mark all the points that is already been
								in some the polygons, for deletion later to further decrease nodes from fort.14.
							1.2 There are no points inside the polygon
								Extract the shoreline of the given town. And check for measurements that are within
								self.radiusOffset meters away. Get maximum of all these measurements.
						Case 2. There are no candidatePoints
							Do Nothing

				'''
				if candidatePoints!=[]:	
					self.filterNodes(parts,geom,candidatePoints,paths,insides)
					for inside in insides:
						for i in range(0,len(inside)):
							if(inside[i]):
								pointIndexInsideGeom.append(candidatePoints_index[i])


					if pointIndexInsideGeom!=[]:
						self.updateWarnings(pointIndexInsideGeom,town_name)

					else:
						pass
						#tanungin kay ma'am kungkailangan niya to. 

						#shoreline=self.getShoreline(geom)
						#shorelineWarnings=self.updateShorelineWarnings(shoreline,candidatePoints,candidatePoints_index)
						#print(shorelineWarnings)	
		

		
		'''
		Checks for all the towns beside a town with warning and mark it for notifications
		'''
		#print(x)
		print("number of Towns:\t"+str(nTowns)+"\t"+"number of Shapes:\t"+str(nShapes)+"\t"+"number of points:\t"+str(nPoints)+"\n" )

		print("Generating notifications")
		self.updateNotifications()


		for i in self.warnings:
			print(i)

		for i in self.notifications:
			print(i)

	def writeToFile(self,directory):
		"""Writes warning to a file with filename <province>.warnings,<province>.notifications. 

		Parameters
		----------
		directory : string
			path to where to place the output file.
		Returns
		-------
		"""

		with open(directory+self.filt+".warnings" , "a") as f:
			print("Storm Surge Warnings: \n")
			f.write("Storm Surge Warnings: \n")
			for i in self.warnings:
				f.write(str(i[2])+","+str(i[0])+"\t"+str(i[1])+"\n")

			f.close()

		with open(directory+self.filt+".notifications" , "a") as f:
			f.write("Storm Surge notifications: \n")			
			for i in self.notifications:
				f.write("Towns/Cities to notify based on "+i[0]+"'s warning:\n")							
				f.write("\t".join(i[1]))
				f.write("\n")
			f.close()

		

	def getEarliestSurge(self):
		"""Get the earliest surge found in a town. 

		Parameters
		----------
		Returns
		-------
		"""

		referenceTime = getReferenceTime(self.fort_15)
		field_names = self.extractFieldNames(self.sf3)

		for r in self.sf3.shapeRecords():
			atr = dict(zip(field_names,r.record))
			geom = r.shape.points
			parts = r.shape.parts		

			if atr['NAME_1'] in self.filt: 
				paths=[]
				insides=[]
				self.filterNodes(parts,geom,[(self.X[i],self.Y[i]) for i in range(1,len(self.X))],paths,insides)

				insides = np.transpose(insides)
				compressedInsides=[]

				for inside in insides:
					if(any(inside)):
						compressedInsides.append(True)
					else:
						compressedInsides.append(False)

				if any(compressedInsides):
					#read for 63
					f=open(self.fort_63,'r')
					print ('Reading fort.63 file')
					tmp=(f.readline()[:-1]).split()
					RUNDES=tmp[0]
					RUNID=tmp[1]
					AGRID=tmp[2]

					tmp=(f.readline()[:-1]).split()
					NDSETSE=int(tmp[0])	#number of iteration*300

					loop=True
					while(loop==True):
						time=f.readline()[:-1].split()
						#print(time)
						time = int(time[1])
						for i in range(0,self.NP):
							tmp = (f.readline()[:-1]).split()
							if(float(tmp[1]) > .1524):
								if(compressedInsides[i]):
									self.earliestSurges.append((atr['NAME_1'],(self.X[i+1],self.Y[i+1]),referenceTime + datetime.timedelta(seconds=time)))


						loop = False
						#print(self.earliestSurges)							

					f.close()
				else:
					print("province out of range")

	def getBarangayOfEarliestSurge(self,directory):
		"""Gets the the barangay location of the earliest surge

		Parameters
		----------
		directory : string
			path to where to place the output file.
		Returns
		-------
		"""

		print("Getting location and time of earliest surges:")

		f=open(directory+self.filt+".warnings" , "w")
		f.write("Earliest Surges: \n")		

		field_names = self.extractFieldNames(self.sf2)
		for r in self.sf2.shapeRecords():
			atr = dict(zip(field_names,r.record))
			#geom = r.shape.points
			#parts = r.shape.parts		
			#[j[0] for j in self.warnings]
			if atr['NAME_1'] == self.filt and atr['NAME_2'] in [j[0] for j in self.warnings]: 
				geom = r.shape.points
				parts = r.shape.parts		

				barangay_name = r.record[8]
				paths=[]
				insides=[]
				self.filterNodes(parts,geom,[info[1] for info in self.earliestSurges],paths,insides)
				
				compressedInsides=[]

				for inside in insides:
					#print(inside)
					if(any(inside)):
						compressedInsides.append(True)
					else:
						compressedInsides.append(False)

				if(any(compressedInsides)):
					print(atr['NAME_3'],atr['NAME_2'],atr['NAME_1'],str(self.earliestSurges[0][2]))

					f.write(atr['NAME_3']+","+atr['NAME_2']+","+atr['NAME_1']+"\t"+str(self.earliestSurges[0][2])+"\n")
		
		f.close()




class MaxKmlGenerator():
	"""
	Responsible for creating kml files for visualization in website.

	"""

	def __init__(self,fort14,maxelev63,typhoonName,eventId,MaxSurgeId,outputDir,shapeFile,filt):
		"""
		Warnings Initialization.
		Initialized given arguments and performs preliminary procedures before warning generations.

		Parameters
		----------
		fort_14 : fort.14 file
			This file includes topography/bathymetry of a bounded area. 
			It also includes the meshes and boundaries needed for the warning generations.
		maxelev63: maxele.63 file
			This file describes provides the maximum elevations at a particular node in the mesh provided by fort_14
		typhoonName: string
			Name of typhoon
		eventId: int
			surge event identification number (corresponds to one fort.14 file)
		MaxSurgeId: int
			maximum elevation identification number (corrensponds to one maxele.63 file)
		outputDir: string
			path for all output files
		shapeFile: string
			.shp file for provinces.
		filt : string
			province filter
		"""

		self.fort14=fort14
		self.maxelev63=maxelev63
		self.typhoonName=typhoonName
		self.eventId=eventId
		self.MaxSurgeId=MaxSurgeId
		self.outputDir=outputDir
		self.shapeFile=shapeFile
		self.filt=filt

	def extractFieldnames(self,sf):
		"""
		Gets the attributes of self.shape_file

		Parameters
		----------
			sf : shapefile.Reader instance
				shapefile parser	
		Returns
		-------
			list
				returns the list of attributes of self.shape_file
		"""	
		fields = sf.fields[1:] 
		return [field[0] for field in fields]

	def filterNodes(self,parts,geom,X,Y,paths,insides):
		"""
		Finds all the points in a given list of points that are inside a polygon.
		For all closed paths. Filter all the points in candidatePoints that are inside that closed paths.
		
		Parameters
		----------
		parts : list
			list of all the closing points of a polygon. It is possible that an administrative boundary can have more than one shapes.
		geom : list
			list of points that bounds a specific town.
		X : list 
			lis of all x-coordinates of all grid points provided by fort.14
		Y : list 
			lis of all y-coordinates of all grid points provided by fort.14
		paths : list
			list of all the paths that defines a polygon
		insides : list
			list of boolean values reflected from candidatePoints. If the value of insides[i] is True then the point candidatePoints[i] is included in a certain polygon.

		Returns
		-------

		"""
		for i in range(0,len(parts)):
			if(i < len(parts) - 1):
				path = mpltPath.Path(geom[parts[i]:parts[i+1]])		
				inside=path.contains_points([(X[j],Y[j]) for j in range(1,len(X))])
				paths.append(path)
				insides.append(inside)
			else:
				path = mpltPath.Path(geom[parts[i]:len(geom)])		
				inside=path.contains_points([(X[j],Y[j]) for j in range(1,len(X))])				
				paths.append(path)
				insides.append(inside)

	def writeToKml(self):
		"""Writes warning to a file with filename <outputDir>maxelev_<typhoonName>_<eventId>_<MaxSurgeId>_<province filter>.kml. 
		   This program checks first if the points in maxele.63 are part of the province filter.
		   If it is, then it converts the measurements into rgb color, and write into kml format.
		   Note: It does not include points with undefined values.

		Parameters
		----------
		Returns
		-------
		"""


		AGRID,NE,NP,X,Y,DP,NM = read_fort14(self.fort14)
		RUNDES,RUNID,AGRID,NDSETSE,ETA = read_maxelev63(self.maxelev63)
		print ('number of elements: ',NE, '\tnumber of Nodes: ',NP)
		
		sf =  shapefile.Reader(self.shapeFile)
		field_names = self.extractFieldnames(sf)

		for r in sf.shapeRecords():
			atr = dict(zip(field_names,r.record))
			geom = r.shape.points
			parts = r.shape.parts		

			if atr['NAME_1'] in self.filt: 
				paths=[]
				insides=[]
				self.filterNodes(parts,geom,X,Y,paths,insides)

				#print ('writing to file '+	)
				if self.typhoonName!="" or self.eventId!="":
					g=open(self.outputDir+"maxelev_"+self.typhoonName+"_"+self.eventId+"_"+self.MaxSurgeId+"_"+atr['NAME_1']+".kml",'w')
				else:
					g=open('temp.kml','w')		

				g.write('<?xml version="1.0" encoding="UTF-8"?>\n')
				g.write('<kml xmlns="http://earth.google.com/kml/2.0"> <Document>\n')
				for k in range(1,NE+1):

					for inside in insides:

						if (inside[NM[k][0]-1]==True or inside[NM[k][1]-1]==True or inside[NM[k][2]-1]==True):
							color='#00ffffff'
							ave=max(ETA[NM[k][0]],ETA[NM[k][1]],ETA[NM[k][2]])
							
							if ave < -1 and ave != -99999:
								R=49
								B=255
								G=49
								color='#a0%02x%02x%02x' % (B,G,R)	
							elif ave >= -1 and ave <0:
								R=49
								B=255
								G=49 + int(((ave-(-1))/(0-(-1)))*(206))
								color='#a0%02x%02x%02x' % (B,G,R)
							elif ave >= 0 and ave <1:
								R=49
								G=255
								B= 255 - int(((ave-0)/(1-0))*(206))
								color='#a0%02x%02x%02x' % (B,G,R)			
							elif ave >= 1 and ave <2:
								B=49
								G=255
								R= 49 + int(((ave-1)/(2-1))*(206))
								color='#a0%02x%02x%02x' % (B,G,R)
							elif ave >=2 and ave < 3:
								R=255
								B=49
								G= 255 - int(((ave-2)/(3-2))*(206))
								color='#a0%02x%02x%02x' % (B,G,R)
							elif ave >=3 and ave <4:
								R=255
								B=49 + int(((ave-3)/(4-3))*(206))
								G=49
								color='#a0%02x%02x%02x' % (B,G,R)				
							elif ave >=4:
								R=255
								B=255
								G=0
								color='#a0%02x%02x%02x' % (B,G,R)
							g.write('<Placemark>\n')
							g.write(' <Polygon> <outerBoundaryIs>  <LinearRing>  \n')
							g.write('  <coordinates>\n')
							g.write('     '+str(X[NM[k][0]])+','+str(Y[NM[k][0]])+'\n')	
							g.write('     '+str(X[NM[k][1]])+','+str(Y[NM[k][1]])+'\n')	
							g.write('     '+str(X[NM[k][2]])+','+str(Y[NM[k][2]])+'\n')	
							g.write('  </coordinates>\n')				
							g.write(' </LinearRing> </outerBoundaryIs> </Polygon>\n')
							g.write(' <Style>\n')
							g.write('  <PolyStyle>\n')
							g.write('   <color>'+color+'</color>\n')
							g.write('  <outline>0</outline>\n')
							g.write('  </PolyStyle>\n')
							g.write(' </Style>\n')
							g.write('</Placemark>\n')

				g.write('</Document> </kml>')
				g.close()							