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
from pyspark import SparkContext, SparkConf

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
    #print ampl
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

def processList(data):
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
                magList.append(local_mag)
            except:
                print "TIMESERIES FAIL", each2
                continue
        if len(magList) > 0:
            retVal = data[6]+ "," + data[0]+ ","+ data[1] +"," +\
                    data[2] +","+ str(np.mean(magList))
                #print retVal
            return retVal
        else:
            return 'FAIL'
    except:
        #print 'SEEDLIST FAIL ', each1[0]
        return 'FAIL'

def main():
    eventID = 4417721
    client = Client("IRIS")
    #cat = client.get_events(eventid=eventID)
    #print cat
    #timeSeriesClient = iris.Client()
    eventLatitude = 40.8287
    eventLongitude = -125.1338
    #eventTime = '2014-03-10T05:18:13.4000'
    eventMagnitude = 7.1
    magUnit = 'MW'
    #dt = UTCDateTime(eventTime)

    ##THIS LIST IS TO BE MADE BY PARSING EVENTS.CSV
    eventList = [('5158626', 25.1395, -109.433, '2015-09-13T08:14:12.2400', 6.7, 'MWW'),\
                 ('4768129', 38.2155, -122.3117, '2014-08-24T10:20:44.0600', 6.02, 'MW'),\
                 ('4311182', 26.0913, -110.3209, '2013-10-19T17:54:54.7000', 6.6, 'MWW'),\
                 ('3318739', 25.09, -109.5366, '2011-07-26T17:44:21.5100', 6.0, 'MW')]

    #reading data from json file
    with open('input.json') as data_file:
        quake_data = json.load(data_file)
    print quake_data
    processedEvent = set()
    if os.path.exists("processedEvent.p"):
        processedEvent = pickle.load('processedEvent.p')
    netStationList = set()
    for each_quake in quake_data:
        eventID = each_quake['EventID']
        if eventID in processedEvent:
            continue
        eventLatitude = each_quake['Latitude']
        eventLongitude = each_quake['Longitude']
        eventTime = each_quake['date']+"T"+each_quake['time']
        for each_net in test:
            try:
                inventory = client.get_stations(network = each_net, latitude=eventLatitude, \
                                        longitude=eventLongitude, maxradius=10)
                #print type(inventory)
                for each in inventory:
                    each_content = each.get_contents()
                    lat, lon = get_coordinates(each[0])
                    channelList = each_content['stations']
                    for each_channel in channelList:
                        randTime = random.randint(1, 6000)
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
    #getting time series data in a loop
    netRDD = sc.parallelize(netStationList)
    outRDD = netRDD.map(processList).filter(lambda x: not x =='FAIL' )
    stationMag = outRDD.collect()
    fStat = open('stationMagnitudes.txt', 'w')
    fStat.write('EventID,NETSTATIONID,LATITUDE,LONGITUDE,MAGNITUDE')
    for each_station in stationMag:
        processedEvent.add(each_station.split(',')[0])
        fStat.write(each_station+"\n")
    #f.write('test')
    fStat.close()
    pickle.dump( processedEvent, open( "processedEvent.p", "w" ) )


    #st = timeSeriesClient.timeseries("AV", "OKSO", '*', "BHZ", dt, dt+10)
test=set(['IU', 'TA'])

USNETS=set(['CU', 'IU', 'II', 'IM', 'AK', 'AT', 'AV', 'AZ', 'BK', 'CI', 'CN', 'EM', 'II', 'IM',\
            'LB', 'LD', 'NY', 'PO', 'TA', 'UO', 'US', 'UU',\
            'X8', 'XA', 'XD', 'XE', 'XG','XI','XN','XO','XQ','XR','XT',\
            'XT','XU','XV','YE','YG','YH','YQ','YT','YW','YX','Z9','ZG',\
            'ZH','ZI','ZK','ZL','ZZ'])

conf = SparkConf()
conf.setMaster("local[4]")
conf.setAppName("reduce")
conf.set("spark.executor.memory", "4g")

sc = SparkContext(conf=conf)

#client = Client("IRIS")

if __name__ == "__main__":
    main()