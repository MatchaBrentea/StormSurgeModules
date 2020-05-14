import sys
import datetime
import shapefile
import numpy as np
import matplotlib.path as mpltPath
from scipy.spatial import distance
from geopy.distance import distance as gdist
from adpy import*




class Warnings:
	'''******************************************************************************************
	<This is a class for generating warning for each barangay in a municipality>
	@parameters:
		shapefile 	: NAME_2e of the shapefile.
		filt 	  	: string that will be used for filtering.
		fort_14		: name of the fort.14 file to be used.
		maxelev63 	: name of the maxele.63 file to be used.
	@notable properties/attributes:
		sf 			: shapefile reader object for accesing shapefile data/geometries.
		NE			: number of elements from fort.14.
		NP			: number of nodes/points from fort.14.
		X,Y			: array X and Y are coordinates of NP points.
		DP 			: topography/bathymetry of each point.
		NM 			: array of 3-ple (describing triangular mesh)
		ETA			: maximum elevations from maxele.63
	@methods:
		getCenter
			---provides the center given a list of points---
			parameters	: arr (array of points)
			return 		: returns the a 2 tuple (center)		
		getDirection 
			---provides the direction of a point with respect to a reference point---
			parameters	: pointA,pointB both 2-tuples (represent the coordinates of 2 points)
			return		: returns one of the directions in the set {N , E , W , S , NE , NW , SE , SW}	
		findMaxDist
			---provides the maximum distance of each points in a set of point with respect to a reference point---
			parameters	: a, arr (reference point,set of points)
			return 		: float distance
		extractFieldNames
			---provides the fields/attributes of a shapefile---
			return 		: list of attributes
		findCandidatePoints
			---provides the list of points  within a given radius with respect to a point---
			parameters	: center,maxDist,candidatePoints,candidatePoints_index (reference point,radius,storing array for points,storing array for points index)
			return 		: returns a list of points and a list of indices
		
	*************************************************************************************************'''


	def __init__(self,shape_file,filt,fort_14,maxelev63,radiusOffset):
		self.shape_file=shape_file
		self.filt=filt
		self.fort_14=fort_14
		self.maxelev63=maxelev63
		self.radiusOffset=radiusOffset

		print("parsing file",datetime.datetime.now())
		self.sf =  shapefile.Reader(self.shape_file)
		self.AGRID,self.NE,self.NP,self.X,self.Y,self.DP,self.NM = read_fort14(self.fort_14)
		self.RUNDES,self.RUNID,self.AGRID,self.NDSETSE,self.ETA = read_maxelev63(self.maxelev63)

		self.warnings=[]
		self.notifications=[]


	def __str__(self):
		return self.shape_file +"\t"+ self.filt +"\t"+ self.fort_14 +"\t"+ self.maxelev63

	
	'''*********************************************************************'''
	'''							helper functions							'''
	'''*********************************************************************'''
	def getCenter(self,arr):
		return (sum([i[0] for i in arr])/len(arr),sum([i[1] for i in arr])/len(arr))

	def findMaxDist(self,a,arr):
		return max([gdist(a,i).meters for i in arr])	

	def getDirection(self,pointA,pointB):
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

	'''*********************************************************************'''
	'''							class  functions							'''
	'''*********************************************************************'''

	def extractFieldNames(self):
		#print("extracting field names",datetime.datetime.now())
		fields = self.sf.fields[1:] 
		field_names = [field[0] for field in fields]
		return field_names


	def findCandidatePoints(self,center,maxDist,candidatePoints,candidatePoints_index):
		for i in range(1,len(self.X)):
			if gdist(center,(self.X[i],self.Y[i])).meters < maxDist:
				if(self.ETA[i]) != -99999:
					candidatePoints.append((self.X[i],self.Y[i]))
					candidatePoints_index.append(i)		


	def updateWarnings(self,pointIndexInsideGeom,barangay_name):
		maxElev=max([self.ETA[i] for i in pointIndexInsideGeom])

		for i in pointIndexInsideGeom:
			self.X[i]=self.Y[i]=self.ETA[i]="rem"
		self.X=list(filter(lambda a: a != "rem", self.X))
		self.Y=list(filter(lambda a: a != "rem", self.Y))
		self.ETA=list(filter(lambda a: a != "rem", self.ETA))
		self.warnings.append((barangay_name,maxElev))
		#print(barangay_name,maxElev)

	def updateNotifications(self,center,candidatePoints,candidatePoints_index,barangay_name):
		#get the value of the nearest point
		disPoints=[gdist(center,i).meters for i in candidatePoints]			
		cPI=candidatePoints_index[(disPoints).index(min(disPoints))]
		maxElev=self.ETA[cPI]
		distance=min(disPoints)
		direction=self.getDirection(center,(self.X[cPI],self.Y[cPI]))
		#print("no  points detected inside the polygon, notification of ",self.ETA[cPI],self.ETA[cPI],min(disPoints),self.getDirection(center,(self.X[cPI],self.Y[cPI])))
		self.notifications.append((barangay_name,maxElev,distance,direction))
		#print(barangay_name,maxElev,distance,direction)


	def filterNodes(self,parts,geom,candidatePoints,paths,insides):
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

	def generateWarnings(self):
		print("generating warning/notifications",datetime.datetime.now())
		
		field_names = self.extractFieldNames()
		#	generate warnings for each barangays...
		for r in self.sf.shapeRecords():

			#	extract information from .shp file
			atr = dict(zip(field_names,r.record))
			#geom = r.shape.points
			#parts = r.shape.parts		

			#	filter shape file with command line argument "filt"
			if atr['NAME_2'] == self.filt: 

				geom = r.shape.points
				parts = r.shape.parts		

				#	find the center of the barangay and the farthest distance of the vertex of the polygon 
				#	describing the barangay
				barangay_name = r.record[8]
				center=self.getCenter(geom)
				maxDist=self.findMaxDist(center,geom)

				paths =[]
				insides=[]


				candidatePoints=[]
				candidatePoints_index=[]
				pointIndexInsideGeom=[]
				#path = mpltPath.Path(geom)

				print(barangay_name)

				'''	iterate over all fort.14 nodes and take note of all the nodes
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
								and update Warnings for barangays. Mark all the points that is already been
								in some the polygons, for deletion later to further nodes from fort.14.
							1.2 There are no points inside the polygon
								Update notification fo the barangay by getting the elevation of the nearest point
								from the center.
						Case 2. There are no candidate points.
							increase maxDist according to the <radiusOffset> and proceed to Case 1.2

				'''
	
				if candidatePoints!=[]:	
					#inside=path.contains_points(candidatePoints) #
					self.filterNodes(parts,geom,candidatePoints,paths,insides)

					#for i in range(0,len(inside)):
					#	if(inside[i]):
					#		pointIndexInsideGeom.append(candidatePoints_index[i])#

					for inside in insides:
						for i in range(0,len(inside)):
							if(inside[i]):
								pointIndexInsideGeom.append(candidatePoints_index[i])


					if pointIndexInsideGeom!=[]:
						self.updateWarnings(pointIndexInsideGeom,barangay_name)

					else:
						self.updateNotifications(center,candidatePoints,candidatePoints_index,barangay_name)
				else:
					self.findCandidatePoints(center,maxDist + self.radiusOffset,candidatePoints,candidatePoints_index)
					if(candidatePoints!=[]):
						self.updateNotifications(center,candidatePoints,candidatePoints_index,barangay_name)

	
	def writeToFile(self,directory):
		with open(directory+self.filt+".warnings" , "a") as f:
			for i in self.warnings:
				f.write(str(i[0])+"\t"+str(i[1])+"\n")

			f.close()

		with open(directory+self.filt+".notifications" , "a") as f:
			for i in self.notifications:
				f.write(str(i[0])+"\t"+str(i[1])+"\t"+str(i[2])+"\t"+str(i[3])+"\n")

			f.close()



class EarliestSurgeLocator():
	def __init__(self,fort14,fort15,fort63,shapeFile,filters):
		self.fort14 = fort14
		self.fort15 = fort15
		self.fort63 = fort63
		self.shapeFile = shapeFile
		self.filters = filters
		self.earliestSurges = []

	def extractFieldnames(self,sf):
		fields = sf.fields[1:] 
		return [field[0] for field in fields]

	def filterNodes(self,parts,geom,X,Y,paths,insides):
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

	def getEarliestSurge(self):
		#get reference time
		#parse fort.14
		referenceTime = getReferenceTime(self.fort15)
		AGRID,NE,NP,X,Y,DP,NM = read_fort14(self.fort14)

		sf =  shapefile.Reader(self.shapeFile)
		field_names = self.extractFieldnames(sf)

		for r in sf.shapeRecords():
			atr = dict(zip(field_names,r.record))
			geom = r.shape.points
			parts = r.shape.parts		

			if atr['NAME_2'] in self.filters: 
				print(atr['NAME_2'])
				paths=[]
				insides=[]
				self.filterNodes(parts,geom,X,Y,paths,insides)

				insides = np.transpose(insides)
				compressedInsides=[]

				for inside in insides:
					#print(inside)
					if(any(inside)):
						compressedInsides.append(True)
					else:
						compressedInsides.append(False)

				if any(compressedInsides):
					#read for 63
					f=open(self.fort63,'r')
					print ('Reading fort.63 file')
					tmp=(f.readline()[:-1]).split()
					RUNDES=tmp[0]
					RUNID=tmp[1]
					AGRID=tmp[2]

					tmp=(f.readline()[:-1]).split()
					NDSETSE=int(tmp[0])	#number of iteration*300

					loop=True
					while(loop):
						time=f.readline()[:-1].split()
						print(time)
						time = int(time[1])
						for i in range(0,NP):
							tmp = (f.readline()[:-1]).split()
							if(float(tmp[1]) > .1524):
								if(compressedInsides[i]):
									self.earliestSurges.append((atr['NAME_2'],(X[i+1],Y[i+1]),referenceTime + datetime.timedelta(seconds=time)))
									loop=False

									break

					f.close()
				else:
					print("municipality out of range")


	def getBarangayOfEarliestSurge(self,barangayShapeFile,directory):
		for i in self.earliestSurges:
			#print(i[0],i[1])
			sf =  shapefile.Reader(barangayShapeFile)
			field_names = self.extractFieldnames(sf)

			for r in sf.shapeRecords():
				atr = dict(zip(field_names,r.record))
				#geom = r.shape.points
				#parts = r.shape.parts		

				if atr['NAME_2'] == i[0]: 

					geom = r.shape.points
					parts = r.shape.parts		

					barangay_name = r.record[8]
					paths=[]
					insides=[]

					for k in range(0,len(parts)):
						if(k < len(parts) - 1):
							path = mpltPath.Path(geom[parts[k]:parts[k+1]])		
							inside=path.contains_points([i[1]])
							paths.append(path)
							insides.append(inside)
						else:
							path = mpltPath.Path(geom[parts[k]:len(geom)])		
							inside=path.contains_points([i[1]])				
							paths.append(path)
							insides.append(inside)					

					compressedInsides=[]

					for inside in insides:
						#print(inside)
						if(any(inside)):
							compressedInsides.append(True)
						else:
							compressedInsides.append(False)

					if(any(compressedInsides)):
						print(i[0],barangay_name,i[2])

						with open(directory+i[0]+".warnings" , "w") as f:
							f.write(str(i[0])+"\t"+ str(barangay_name)+"\t"+str(i[2])+"\n")
							f.close()

						break