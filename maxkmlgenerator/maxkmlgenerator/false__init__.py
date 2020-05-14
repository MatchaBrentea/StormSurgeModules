#!/usr/bin/python

import sys
sys.path.append(r"C:\Users\adminalpha\Desktop\UPStuff\Acads\1920A\ThesisRelated\StormSurge2019\Modules\maxkmlgenerator\maxkmlgenerator")
import shapefile
import matplotlib.path as mpltPath
from adpy import*

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

		self.fort14=fort14
		self.maxelev63=maxelev63
		self.typhoonName=typhoonName
		self.eventId=eventId
		self.MaxSurgeId=MaxSurgeId
		self.outputDir=outputDir
		self.shapeFile=shapeFile
		self.filt=filt

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

	def writeToKml(self):
		AGRID,NE,NP,X,Y,DP,NM = read_fort14(self.fort14)
		RUNDES,RUNID,AGRID,NDSETSE,ETA = read_maxelev63(self.maxelev63)
		print ('number of elements: ',NE, '\tnumber of Nodes: ',NP)
		print("ETA: ",len(ETA),"X:",len(X),"Y: ",len(Y))
		final_str = ""

		sf =  shapefile.Reader(self.shapeFile)
		
		field_names = self.extractFieldnames(sf)
		
		for r in sf.shapeRecords():			
			x = 0
			atr = dict(zip(field_names,r.record))
			geom = r.shape.points
			parts = r.shape.parts
			print(r)
			x = 0
			paths=[]
			insides=[]
			self.filterNodes(parts,geom,X,Y,paths,insides)
			#print ('writing to file '+	)
			if self.typhoonName!="" or self.eventId!="":
				g=open("maxelev_"+self.typhoonName+"_"+self.eventId+"_"+self.MaxSurgeId+"_"+atr['NAME_1']+".geojson",'w+')
			else:
				g=open('temp.kml','w+')

			g.write('{"type": "FeatureCollection",\n"features" :[\n')						
			for k in range(1,NE+1):
				for inside in insides:
						x = 1
						color='#ffffff'
						final_str+='{\n"type": "Feature",\n'
						final_str+='"geometry": {\n'
						final_str+='"type": "Polygon",\n'
						final_str+='"coordinates": [\n'
						final_str+='[\n'
						final_str+= '[\n'+str(X[NM[k][0]])+',\n'+str(Y[NM[k][0]])+'\n],\n'
						final_str+= '[\n'+str(X[NM[k][1]])+',\n'+str(Y[NM[k][1]])+'\n],\n'
						final_str+= '[\n'+str(X[NM[k][2]])+',\n'+str(Y[NM[k][2]])+'\n]\n'
						final_str+= ']\n]\n},\n'
						final_str+= '"properties": {\n'
						final_str+= '"fill": "'+color+'",\n'
						final_str+= '"fill-opacity": 0.6274509803921569,\n'
						final_str+= '"stroke-opacity": 0\n'
						final_str+= '}\n},\n'
			g.write(final_str)
			g.write(']\n}')
			g.close()
			