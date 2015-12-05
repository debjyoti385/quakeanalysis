'''from obspy.fdsn.client import Client
from obspy import iris
from obspy import arclink
from obspy import UTCDateTime


client = Client("IRIS")
iClient = iris.Client()
arcClient = arclink.Client(user="sed-workshop@obspy.org")
timeSeriesClient = iris.Client()
t1 = UTCDateTime("2012-04-12T07:15:49.1700")
#t1 = UTCDateTime("1994-09-12T12:23:43.630000")
t2 = t1 + 5
st =iClient.getWaveform("CI", "BAR", "??", "BHZ", t1, t2)
print "waveform"
tr = st.select(station="BAR")[0]
print tr
#s1=st[0].stats.coordinates.latitude
#s2=st[0].stats.coordinates.longitude
#print s1, s2'''

'''from math import log10

import numpy as np

from obspy.arclink import Client
from obspy.core import UTCDateTime
from obspy.core.util.geodetics import gps2DistAzimuth


paz_wa = {'sensitivity': 2800, 'zeros': [0j], 'gain': 1,
          'poles': [-6.2832 - 4.7124j, -6.2832 + 4.7124j]}

client = Client(user="sed-workshop@obspy.org")
t = UTCDateTime("2012-04-03T02:45:03")

stations = client.getStations(t, t + 300, "BC")'''

from obspy.fdsn.client import Client
from obspy import UTCDateTime
from obspy.core import read

client = Client("IRIS")
t1 = UTCDateTime("2012-04-12T07:15:49.1700")
#IU.TUC.20.LNZ
st = client.get_waveforms("IU", "ANMO", "00", "BH?", t1, t1 + 4 * 3600)
st.detrend(type='demean')
for each in st:
    ampl = each.data
    print max(abs(ampl))
'''tr_n = st.select(component="N")[0]
ampl_n = max(abs(tr_n.data))

tr_e = st.select(component="E")[0]
ampl_e = max(abs(tr_e.data))

ampl = max(ampl_n, ampl_e)'''


st = read("/Users/zinniamukherjee/Education/BigData/Project/MagnitudeCalculator/LKBD_WA_CUT.MSEED")
st.detrend(type='demean')
ampl = st[0].data
print max(abs(ampl))
tr_n = st.select(component="N")[0]
ampl_n = max(abs(tr_n.data))
print ampl_n
tr_e = st.select(component="E")[0]
ampl_e = max(abs(tr_e.data))
ampl = max(ampl_n, ampl_e)
print ampl_e

