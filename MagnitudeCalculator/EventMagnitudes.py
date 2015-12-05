from obspy.fdsn.client import Client

from obspy import iris
from obspy import arclink
from obspy import UTCDateTime
from math import log10
from obspy.core.util.geodetics import gps2DistAzimuth
from obspy.core.util import NamedTemporaryFile
import numpy as np
import re


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
    '''ampl_n = 0
    ampl_e = 0
    tr_n = st.select(component="N")
    if tr_n != None or len(tr_n)>0:
        ampl_n = max(abs(tr_n[0].data))

    tr_e = st.select(component="E")
    if tr_e != None or len(tr_e)>0:
        ampl_e = max(abs(tr_e[0].data))

    ampl = max(ampl_n, ampl_e)'''

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




def main():
    eventID = 4417721
    client = Client("IRIS")
    cat = client.get_events(eventid=eventID)
    #print cat
    timeSeriesClient = iris.Client()
    eventLatitude = 40.8287
    eventLongitude = -125.1338
    eventTime = '2012-04-12T07:15:49.1700'
    eventMagnitude = 7.1
    magUnit = 'MW'
    dt = UTCDateTime(eventTime)
    print "EARTHQUAKE", str(eventLatitude), str(eventLongitude), str(eventMagnitude)+" "+ magUnit
    netStationList = set()
    #getting list of stations for US networks
    for each_net in USNETS:
        try:
            inventory = client.get_stations(network = each_net, latitude=eventLatitude,\
                                            longitude=eventLongitude, maxradius=5)
            #print type(inventory)
            for each in inventory:
                each_content = each.get_contents()
                lat, lon = get_coordinates(each[0])
                channelList = each_content['stations']
                for each_channel in channelList:
                    netStationList.add((each_channel.split()[0], lat, lon))
        except:
            #print "Failed for", each_net
            continue

    #print inventory.get_contents()
    #print netStationList
    #getting time series data in a loop



    for each1 in netStationList:
        netStation = each1[0].split('.')
        network = netStation[0]
        station = netStation[1]
        magList = []
        try:
            data = timeSeriesClient.resp(network, station, '*', '*', dt)
            #print "SEEDLIST SUCCESS ", each1[0]
            seedList = parseResponse(data.decode())
            for each2 in seedList:
                arr = each2.split('.')
                try:
                    st = client.get_waveforms(arr[0], arr[1], arr[2], arr[3], dt, dt+1800)
                    #print "TIMESERIES SUCCESS", each2
                    ampl = get_amplitude(st, dt, each2)
                    local_mag = calculate_local_magnitude(eventLatitude, eventLongitude, each1[1], each1[2], ampl)
                    magList.append(local_mag)
                    #print each2, each1[1], each1[2], local_mag
                    #print "TIMESERIES SUCCESS", each2
                except:
                    #print "TIMESERIES FAIL", each2
                    continue
            if len(magList) > 0:
                print each1[0], each1[1], each1[2], sum(magList)/float(len(magList))

        except:
            #print 'SEEDLIST FAIL ', each1[0]
            continue

    #st = timeSeriesClient.timeseries("AV", "OKSO", '*', "BHZ", dt, dt+10)
test=set(['IU'])

USNETS=set(['CU', 'IU', 'II', 'IM', 'AK', 'AT', 'AV', 'AZ', 'BK', 'CI', 'CN', 'EM', 'II', 'IM',\
            'LB', 'LD', 'NN', 'NY', 'PO', 'TA', 'UO', 'US', 'UU',\
            'X8', 'XA', 'XD', 'XE', 'XG','XI','XN','XO','XQ','XR','XT',\
            'XT','XU','XV','YE','YG','YH','YQ','YT','YW','YX','Z9','ZG',\
            'ZH','ZI','ZK','ZL','ZZ'])

if __name__ == "__main__":
    main()