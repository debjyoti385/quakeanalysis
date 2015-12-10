from obspy.fdsn.client import Client

from obspy import iris
from obspy import UTCDateTime
from math import log10
from obspy.core.util.geodetics import gps2DistAzimuth
from obspy.core.util import NamedTemporaryFile
import numpy as np
import re
import random
import time
import json
import pickle
import os.path

def parseResponse(data):
    #print data
    seedList = set()
    dataArr = data.split('\n')
    S = ''
    C = ''
    N = ''
    L = ''
    no_of_infos = 0
    netPattern = re.compile(".*Network:[\s]*(.*)")
    statPattern = re.compile(".*Station:[\s]*(.*)")
    locPattern = re.compile(".*Location:[\s]*(.*)")
    chPattern = re.compile(".*Channel:[\s]*(.*)")
    for each_line in dataArr:
        if no_of_infos == 0:
            S = ''
            C = ''
            N = ''
            L = ''
        netMatch = netPattern.match(each_line)
        statMatch = statPattern.match(each_line)
        locMatch = locPattern.match(each_line)
        chMatch = chPattern.match(each_line)
        if netMatch != None:
            N = netMatch.groups()[0]
            no_of_infos += 1
        elif statMatch != None:
            S = statMatch.groups()[0]
            no_of_infos += 1
        elif locMatch != None:
            L = locMatch.groups()[0]
            no_of_infos += 1
        elif chMatch != None:
            C = chMatch.groups()[0]
            C = C[:-1]+'?'
            no_of_infos += 1
        if no_of_infos == 4:
            seedList.add(N+'.'+S+'.'+L+'.'+C)
            no_of_infos = 0
    return seedList


def get_coordinates(data):
    dataArr = str(data).split('\n')
    #print dataArr
    coordPattern = re.compile("[\s]*Latitude:\s(.*),\sLongitude:\s(.*),")
    for each_line in dataArr:
        #print each_line
        lineMatch = coordPattern.match(each_line)
        if lineMatch!=None:
            return lineMatch.groups()[0], lineMatch.groups()[1]

def get_amplitude(st, dt, seed_id):

    #stream correcting
    with NamedTemporaryFile() as tf:
        respf = tf.name
        old_iris_client = iris.Client()
    # fetch RESP information from "old" IRIS web service, see obspy.fdsn
    # for accessing the new IRIS FDSN web services
        arr=seed_id.split('.')
        old_iris_client.resp(arr[0], arr[1], arr[2], arr[3], dt, dt+1800, filename=respf)

    # make a copy to keep our original data
        st_orig = st.copy()

    # define a filter band to prevent amplifying noise during the deconvolution
        pre_filt = (0.005, 0.006, 30.0, 35.0)

    # this can be the date of your raw data or any date for which the
    # SEED RESP-file is valid
        date = dt

        seedresp = {'filename': respf,  # RESP filename
                # when using Trace/Stream.simulate() the "date" parameter can
                # also be omitted, and the starttime of the trace is then used.
                'date': date,
                # Units to return response in ('DIS', 'VEL' or ACC)
                'units': 'DIS'
                }

    # Remove instrument response using the information from the given RESP file
        st.simulate(paz_remove=None, pre_filt=pre_filt, seedresp=seedresp)


    ####################
    ampl = max(abs(st[0].data))
    for each in st:
        a = max(abs(each.data))
        if a > ampl:
            ampl = a
    print ampl
    return ampl

def calculate_local_magnitude(eventLat, eventLon, sta_lat, sta_lon, ampl):
    #print "Try"
    epi_dist, az, baz = gps2DistAzimuth(eventLat, eventLon, float(sta_lat), float(sta_lon))
    epi_dist = epi_dist / 1000
    #print "Azi dist", epi_dist
    if epi_dist > 60:
        a = 0.0037
        b = 3.02
    else:
        a = 0.018
        b = 2.17
    ml = log10(ampl * 1000) + a * epi_dist + b
    #print 'magnitude', ml
    return ml

def processNetStationList(data):
    #print data[0]
    print "SLEEP", data[6], data[7]
    time.sleep(float(data[7]/1000))
    dt = UTCDateTime(data[5])
    timeSeriesClient = iris.Client()
    client = Client("IRIS")
    netStation = data[0].split('.')
    network = netStation[0]
    station = netStation[1]
    magList = []
    try:
        respData = timeSeriesClient.resp(network, station, '*', '*', dt)
        #print "SEEDLIST SUCCESS ", respData[0]
        seedList = parseResponse(respData.decode())
        for each2 in seedList:
            arr = each2.split('.')
            try:
                st = client.get_waveforms(arr[0], arr[1], arr[2], arr[3], dt, dt+1800)
                print "TIMESERIES SUCCESS", each2
                ampl = get_amplitude(st, dt, each2)
                local_mag = calculate_local_magnitude(data[3], data[4], data[1], data[2], ampl)
                #print local_mag
                magList.append(local_mag)
                #print "Appended to magnitude list"
            except:
                #print "TIMESERIES FAIL", each2
                continue
        print magList
        if len(magList) > 0:
            #print "Magnitude list obtained"
            retVal = str(data[6])+ "," + data[0]+ ","+ data[1] +"," +\
                    data[2] +","+ str(sum(magList)/float(len(magList)))
            #print "Returning value:", retVal

            return retVal
        else:
            return 'FAIL'

    except:
        print 'SEEDLIST FAIL ', data[0]
        return 'FAIL'




def processEvents(quake_data, client, processedEvent):
    netStationList = set()
    out_res=[]
    fStat = open('stationMagnitudes.txt', 'a')
    for each_quake in quake_data:
        eventID = each_quake['EventID']
        eventLatitude = float(each_quake['Latitude'])
        eventLongitude = float(each_quake['Longitude'])
        eventTime = each_quake['date-time']
        processedEvent.add(str(eventID))
        write_event_info_line = str(eventID) +","+"QUAKE,"+str(eventLatitude)+\
            ","+str(eventLongitude)+","+str(each_quake['Magnitude'])
        out_res.append(write_event_info_line)
        fStat.write(write_event_info_line+"\n")
        for each_net in USNETS:
            try:
                inventory = client.get_stations(network = each_net, latitude=eventLatitude, \
                                        longitude=eventLongitude, maxradius=10)
                #print type(inventory)
                for each in inventory:
                    each_content = each.get_contents()
                    lat, lon = get_coordinates(each[0])
                    channelList = each_content['stations']
                    for each_channel in channelList:
                        randTime = random.randint(1, 10)
                        netStationList.add((each_channel.split()[0], lat, lon,eventLatitude,\
                                            eventLongitude, eventTime, eventID, randTime))
            except:
                #print "Failed for", each_net
                continue


    #print "EARTHQUAKE", str(eventLatitude), str(eventLongitude), str(eventMagnitude), magUnit

    #getting list of stations for US networks
    #print USNETS

    #print inventory.get_contents()
    print "LENGTH OF NET STATION", len(netStationList)
    fStat.close()
    #getting time series data in a loop
    netRDD = sc.parallelize(netStationList)
    outRDD = netRDD.map(processNetStationList).filter(lambda x: not x =='FAIL' )
    stationMag = outRDD.collect()
    print stationMag
    fStat = open('stationMagnitudes.txt', 'a')
    #fStat.write('EventID,NETSTATIONID,LATITUDE,LONGITUDE,MAGNITUDE'+"\n")
    for each_station in stationMag:
        fStat.write(each_station+"\n")
        out_res.append(each_station)
    #f.write('test')
    fStat.close()
    pickleWrite = open( "processedEvent.p", "w" )
    pickle.dump( processedEvent, pickleWrite)
    pickleWrite.close()
    return out_res

def generate_events(spark_context, eventList):
    global sc
    sc = spark_context
    quake_data = list()
    client = Client("IRIS")
    processedEvent = set()
    if os.path.exists("processedEvent.p"):
        pickleFile = open('processedEvent.p', 'rb')
        processedEvent = pickle.load(pickleFile)
        pickleFile.close()
    for each_event in eventList:
        if each_event in processedEvent:
            continue
        cat = client.get_events(eventid=int(each_event))
        eventDict = dict()
        for each_entry in cat:
            event_info = re.compile("Event:\t(.*)\n").match(str(each_entry)).groups()[0]
            event_info_list = event_info.split('|')
            eventDict['date-time'] = event_info_list[0].rstrip().lstrip()
            eventDict['EventID'] = each_event
            origin_info = event_info_list[1].split(',')
            eventDict['Latitude'] = origin_info[0].rstrip().lstrip()
            eventDict['Longitude'] = origin_info[1].rstrip().lstrip()
            eventDict['Magnitude'] = event_info_list[2].split()[0].rstrip().lstrip()
        quake_data.append(eventDict)
    return processEvents(quake_data, client, processedEvent)


test=set(['IU'])

USNETS=set(['CU', 'IU', 'II', 'IM', 'AK', 'AT', 'AV', 'AZ', 'BK', 'CI', 'CN', 'EM', 'II', 'IM',\
            'LB', 'LD', 'NY', 'PO', 'TA', 'UO', 'US', 'UU',\
            'X8', 'XA', 'XD', 'XE', 'XG','XI','XN','XO','XQ','XR','XT',\
            'XT','XU','XV','YE','YG','YH','YQ','YT','YW','YX','Z9','ZG',\
            'ZH','ZI','ZK','ZL','ZZ'])
