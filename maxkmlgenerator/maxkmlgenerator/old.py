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

			if atr['NAME_1'] in self.filt:
				x = 0
				paths=[]
				insides=[]
				self.filterNodes(parts,geom,X,Y,paths,insides)
				#print ('writing to file '+	)
				if self.typhoonName!="" or self.eventId!="":
					g=open(self.outputDir+"maxelev_"+self.typhoonName+"_"+self.eventId+"_"+self.MaxSurgeId+"_"+atr['NAME_1']+".kml",'w+')
				else:
					g=open('temp.kml','w+')

				g.write('<?xml version="1.0" encoding="UTF-8"?>\n')
				g.write('<kml xmlns="http://earth.google.com/kml/2.0"> <Document>\n')
						
				for k in range(1,NE+1):

					for inside in insides:
						if (inside[NM[k][0]-1]==True or inside[NM[k][1]-1]==True or inside[NM[k][2]-1]==True):
							x = 1
							color='#00ffffff'
							ave=max(ETA[NM[k][0]],ETA[NM[k][1]],ETA[NM[k][2]])
							# print("ave: ",ave)	
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
							
							final_str+='<Placemark>\n'
							final_str+=' <Polygon> <outerBoundaryIs>  <LinearRing>  \n'
							final_str+='  <coordinates>\n'
							final_str+='     '+str(X[NM[k][0]])+','+str(Y[NM[k][0]])+'\n'
							final_str+='     '+str(X[NM[k][1]])+','+str(Y[NM[k][1]])+'\n'
							final_str+='     '+str(X[NM[k][2]])+','+str(Y[NM[k][2]])+'\n'
							final_str+='  </coordinates>\n'
							final_str+=' </LinearRing> </outerBoundaryIs> </Polygon>\n'
							final_str+=' <Style>\n'
							final_str+='  <PolyStyle>\n'
							final_str+='   <color>'+color+'</color>\n'
							final_str+='  <outline>0</outline>\n'
							final_str+='  </PolyStyle>\n'
							final_str+=' </Style>\n'
							final_str+='</Placemark>\n'
				g.write(final_str)
				g.write('</Document> </kml>')
				g.close()
				