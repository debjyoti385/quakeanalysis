from xml.dom import minidom
import sys
import re
import csv
import os.path

def processTime(time):
    year = re.search("^(.+?)-", time).group(1)
    month = re.search("-(.+?)-", time).group(1)
    day = re.search("-[0-9]{1,2}-(.+?)T", time).group(1)
    date = re.search("^(.+?)T", time).group(1)
    time = re.search("T(.+?)$", time).group(1)
    return date, year, month, day, time

eventsDoc = minidom.parse(sys.argv[1])

filecheck=1
if len(sys.argv) >3:
    if sys.argv[3]==1:
        filecheck=0

if os.path.isfile(sys.argv[2]) and filecheck==1:
    exit()

events = eventsDoc.getElementsByTagName("event")
count =0
with open(sys.argv[2], 'wb') as csvfile:
    eventwriter = csv.writer(csvfile, delimiter=',')
    eventwriter.writerow(['EventID', 'EventType', 'RegionType', 'Region', 'Fulltime', 'Date', 'Year', 'Month', 'Day', 'Time',\
                         'Latitude', 'Longitude', 'Depth', 'Magnitude', 'MagnitudeUnit'])
    rowValues = []
    for eachEvent in events:
        del rowValues[:]
        eventPublicID = eachEvent.getAttribute("publicID")
        eventID = re.search("eventid=(.+?)$", eventPublicID).group(1)
        rowValues.append(eventID)
        eventType = eachEvent.getElementsByTagName("type")[0].firstChild.data
        rowValues.append(eventType)
        #event description
        eventDescription = eachEvent.getElementsByTagName("description")
        regionType = eventDescription[0].getElementsByTagName("type")[0].firstChild.data
        rowValues.append(regionType)
        region = eventDescription[0].getElementsByTagName("text")[0].firstChild.data
        rowValues.append(region)
        #event origin
        eventOrigin = eachEvent.getElementsByTagName("origin")[0]
        eventTime = eventOrigin.getElementsByTagName("time")[0].getElementsByTagName("value")[0].firstChild.data
        date, year, month, day, time = processTime(eventTime)

        rowValues.append(eventTime)
        rowValues.append(date)
        rowValues.append(year)
        rowValues.append(month)
        rowValues.append(day)
        rowValues.append(time)
        eventLatitude = eventOrigin.getElementsByTagName("latitude")[0].getElementsByTagName("value")[0].firstChild.data
        rowValues.append(eventLatitude)
        eventLongitude = eventOrigin.getElementsByTagName("longitude")[0].getElementsByTagName("value")[0].firstChild.data
        rowValues.append(eventLongitude)
        try:
	    eventDepth = eventOrigin.getElementsByTagName("depth")[0].getElementsByTagName("value")[0].firstChild.data
        except:
            eventDepth = 0.0
        rowValues.append(eventDepth)
        #event maginitude
        eventMagnitude = eachEvent.getElementsByTagName("magnitude")
        if len(eventMagnitude) > 0:
            eventMagValue = eventMagnitude[0].getElementsByTagName("mag")[0].getElementsByTagName("value")[0].firstChild.data
            try:
                eventMagUnit = eventMagnitude[0].getElementsByTagName("type")[0].firstChild.data
            except:
                eventMagUnit = "MB"
            rowValues.append(eventMagValue)
            rowValues.append(eventMagUnit)
        else:
            rowValues.append("")
            rowValues.append('')
        count+=1
        if count %100 ==0:
            print count
        eventwriter.writerow(rowValues)
