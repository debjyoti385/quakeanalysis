
import time, sys, cherrypy, os
#from paste.translogger import TransLogger
from app import create_app
from pyspark import SparkContext, SparkConf

def init_spark_context():
    # load spark context
    conf = SparkConf().setAppName("event-contour-server")
    conf.setMaster("local[4]")
    conf.setAppName("reduce")
    conf.set("spark.executor.memory", "4g")
    # IMPORTANT: pass aditional Python modules to each worker
    sc = SparkContext(conf=conf, pyFiles=['app.py', 'contourGenerator.py','EventParallelize.py'])
 
    return sc
 
 
def run_server(app):
 
    # Enable WSGI access logging via Paste
    #app_logged = TransLogger(app)
 
    # Mount the WSGI callable object (app) on the root directory
    cherrypy.tree.graft(app, '/')
 
    # Set the configuration of the web server
    cherrypy.config.update({
        'engine.autoreload.on': True,
        'log.screen': True,
        'server.socket_port': 5432,
        'server.socket_host': '0.0.0.0'
    })
 
    # Start the CherryPy WSGI web server
    cherrypy.engine.start()
    cherrypy.engine.block()
 
 
if __name__ == "__main__":
    # Init spark context and load libraries
    sc = init_spark_context()
    #read station magnitudes file
    outFile = open('stationMagnitudes.txt', 'rb')
    first_line = True
    stationMagList = list()
    for each_line in outFile:
        if first_line:
            first_line = False
            continue
        stationMagList.append(each_line.rstrip().split(','))

    app = create_app(sc, stationMagList)

 
    # start web server
    run_server(app)