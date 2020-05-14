import datetime

def read_fort14(file):
	#open fort.14 file
	#Brent: fort.14 file is a bunch of matrix numbers 
	f=open(file,'r')
	#print('Reading fort.14 file')

	#parse the file accordingly
	AGRID=(f.readline())[:-1]  #Descriptor
	tmp=(f.readline()[:-1]).split()

	NE=int(tmp[0]) #number of element
	NP=int(tmp[1]) #number of nodes

	X=['X'] 	#X coordinates of Nodes
	Y=['Y']		#Y coordinates of Nodes
	DP=['DP']	#bathymetric depths of Nodes
	ETA=['Elevation']

	for i in range(0,NP):
		tmp=(f.readline()[:-1]).split()
		X.append(float(tmp[1]))
		Y.append(float(tmp[2]))
		DP.append(float(tmp[3]))
	
	NM=[['NM(JE,1)','NM(JE,2)','NM(JE,3)']]		#connections

	for i in range(0,NE):
		tmp=(f.readline()[:-1]).split()
		NM.append([int(tmp[2]),int(tmp[3]),int(tmp[4])])

	f.close()

	return AGRID,NE,NP,X,Y,DP,NM #return variables

def read_maxelev63(file):
	#open maxelev.63
	f=open(file,'r')

	ETA=['Elevation']
	tmp=(f.readline()[:-1]).split()
	RUNDES=tmp[0]
	RUNID=tmp[1]
	AGRID=tmp[2]

	tmp=(f.readline()[:-1]).split()
	NP=int(tmp[1])
	tmp=(f.readline()[:-1]).split()
	NDSETSE=int(tmp[1])	#number of iteration*300



	for j in range(0,NP):
		tmp=(f.readline()[:-1]).split()
		ETA.append(float(tmp[1]))	

	return RUNDES,RUNID,AGRID,NDSETSE,ETA
	f.close()

def getReferenceTime(fort15):
	f=open(fort15,'r')

	for i in range(0,7):
		f.readline()
	IM=(f.readline()[:-1]).split()
	#print(int(IM[0]))
	if(int(IM[0])==21):
		f.readline()
	for i in range(0,4):
		f.readline()
	NWP=(f.readline()[:-1]).split()
	#print(int(NWP[0]))
	for i in range(0,int(NWP[0])):
		f.readline()
	for i in range(0,5):
		f.readline()
	TAUO=(f.readline()[:-1]).split()
	#print(int(TAUO[0]))
	if(int(TAUO[0])==-5.0):
		f.readline()
	for i in range(0,3):
		f.readline()
	WTIMINC=(f.readline()[:-1]).split()
	#print(WTIMINC)
	referenceTime=datetime.datetime(int(WTIMINC[0]),int(WTIMINC[1]),int(WTIMINC[2]),int(WTIMINC[3]))
	print(referenceTime)
	return referenceTime

def getSimulationDuration(fort15):
	f=open(fort15,'r')

	for i in range(0,7):
		f.readline()
	IM=(f.readline()[:-1]).split()
	#print(int(IM[0]))
	if(int(IM[0])==21):
		f.readline()
	for i in range(0,4):
		f.readline()
	NWP=(f.readline()[:-1]).split()
	#print(int(NWP[0]))
	for i in range(0,int(NWP[0])):
		f.readline()
	for i in range(0,5):
		f.readline()
	TAUO=(f.readline()[:-1]).split()
	#print(int(TAUO[0]))
	if(int(TAUO[0])==-5.0):
		f.readline()
	for i in range(0,3):
		f.readline()
	WTIMINC=(f.readline()[:-1]).split()
	#print(WTIMINC)
	referenceTime=datetime.datetime(int(WTIMINC[0]),int(WTIMINC[1]),int(WTIMINC[2]),int(WTIMINC[3]))
	RNDAY = (f.readline()[:-1]).split()
	simulationDuration = float(RNDAY[0])
	return simulationDuration
