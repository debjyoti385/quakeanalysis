import json
import sys
from pprint import pprint

globe = []
for i in range(int(sys.argv[1]),int(sys.argv[2])+1):
    filename = "facts?cut=year:" + str(i)
    print filename
    with open(filename) as data_file:    
        raw = json.load(data_file)

    data=[]
    for e in raw:
        data.append(e['lat'])
        data.append(e['long'])
        data.append(e['scale'] / float(14.24))
    year = str(i) 

    element = []
    element.append(year)
    element.append(data)
    globe.append(element)


globe = json.dumps(globe)

with open("data.json",'w') as writefile:
    writefile.write(globe)
