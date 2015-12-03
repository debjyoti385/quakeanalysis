QuakeAnalysis Event Server
==============================

Files
-----

This directory contains following files:

    * model.json      - logical model
    * slicer.ini      - server configuration file
    * data.csv        - raw data of events [Google Drive Link](https://drive.google.com/open?id=0B7MJnptUCNQPZGZzQzBQUURSYVE){:target="_blank"}
    * data.sqlite     - database, just place it in the folder and you won't require prepare_data step 
                      - [Google Drive Link](https://drive.google.com/open?id=0B7MJnptUCNQPQl8zLTU2VE51cjg){:target="_blank"}
    * prepare_data.py - script for preparing the data: load them into database
                        and create a view
    * aggregate.py    - example aggregations
    * requirements.sh - Install all the pip requirements 
Quick start
-----------

Prepare data::
This will create data.sqlite file (i.e. the database )
`
    python2.7 prepare_data.py data.csv 1
`   

Get some aggregations::
`
    python2.7 aggregate.py
`

Web Server
-------------

Run the server::

    slicer serve slicer.ini
    
Try the server. Aggregate::

  curl "http://localhost:5050/cube/quake_events/aggregate"
    
Aggregate by year::

  curl "http://localhost:5050/cube/quake_events/aggregate?drilldown=year"

Aggregate by year and month::

  curl "http://localhost:5050/cube/quake_events/aggregate?drilldown=year|month"

Apply cuts on earthquake events based on richter scale and latitude::

  curl "http://localhost:5050/cube/quake_events/facts?cut=scale:6-10|lat:24.126701958681682-27.067626642387374"

Apply cuts on earthquake events based on richter scale, latitude and longitude with negative value ranges::

  curl "http://localhost:5050/cube/quake_events/facts?cut=scale:6-10|lat:24.126701958681682-27.067626642387374&cut=long:\-120-\-100"

Note the implicit hierarchy of the `parameter` dimension.

See also the Slicer server documentation for more types of requests:
http://packages.python.org/cubes/server.html

Credits
-------

- [python cube](http://cubes.databrewery.org/){:target="_blank"}
- [IRIS webservices][http://service.iris.edu/]{:target="_blank"}


