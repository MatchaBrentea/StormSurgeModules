import string

def read_file(filename):
	l = 0
	add = 0

	start_x = 1
	end_x = 20
	start_y = 21
	end_y = 40

	with open(filename,'r') as input:
		for line in input:
			l+=1
			if 'break' in line:
				break
			if (l>=3): 
				if(l<=11):
					add=1
				elif(l>=12 and l<=101):
					add=2
				elif(l>=102 and l<=1001):
					add=3
				else:
					add=4
				x.append(line[start_x+add:end_x+add])
				y.append(line[start_y+add:end_y+add])

	return x,y 

def triangle(filename,):
	l = 0
	add = 0
	read_flag = 0
	arr_temp=[]
	start = 3
	with open(filename,'r') as input:
		for line in input:
			l+=1
			if 'end' in line:
				break
			if (read_flag==1):
				if(l<=4880):
					add=1
				elif(l>=4881 and l<=4970):
					add=2
				elif(l>=4971 and l<=5870):
					add=3
				else:
					add=4
				arr_temp.append(line[start+add:])
			if 'break' in line:	
				read_flag=1

	arr_triangle=[]	
	arr_arr=0
	for i in arr_temp:
		text=''
		arr_triangle.append([])
		for j in i:
			if(j=="\t" or j=="\n"):
				arr_triangle[arr_arr].append(text)
				text=''
			else:
				text=text+j
		arr_arr+=1
	return arr_triangle
	

def err_check(x,y):
	err=0
	for i in x:
		if(len(i)!=19):
			err+=1
			print("wrong parsing: ",err)
	for i in y:
		if(len(i)!=19):
			err+=1
			print("wrong parsing: ",err)


if __name__ == '__main__':
	filename = "fort_anim.14"
	x=[]
	y=[]
	arr_x=[]
	arr_y=[]

	x,y=read_file(filename)
	arr_triangle=triangle(filename)

	final_str=''
	g=open("inundation_Haiyan.geojson",'w+')
	g.write('{"type": "FeatureCollection",\n"features" :[\n')


	for i in range(0,len(arr_triangle)-2): 
		final_str+= '{\n"id": '+str(i)+','
		final_str+='\n"type": "Feature",\n'
		final_str+='"geometry": {\n'
		final_str+='"type": "Polygon",\n'
		final_str+='"coordinates": [\n'
		final_str+='[\n'
		final_str+= '[\n'+x[int(arr_triangle[i][0])]+',\n'+y[int(arr_triangle[i][0])]+'\n],\n'
		final_str+= '[\n'+x[int(arr_triangle[i][1])]+',\n'+y[int(arr_triangle[i][1])]+'\n],\n'
		final_str+= '[\n'+x[int(arr_triangle[i][2])]+',\n'+y[int(arr_triangle[i][2])]+'\n]\n'
		final_str+= ']\n]\n},\n'
		final_str+= '"properties": {\n'
		final_str+= '"fill": "'+'#3ab6bd'+'",\n'
		final_str+= '"fill-opacity": 0.6274509803921569,\n'
		final_str+= '"stroke-opacity": 0\n'
		final_str+= '}\n},\n'
		i=i+3
	g.write(final_str)
	g.write(']\n}')
	g.close()
	
		
