# -*- coding: utf-8 -*-
# Data preparation for the hello_world example
from __future__ import print_function

from sqlalchemy import create_engine
from cubes.tutorial.sql import create_table_from_csv
import sys
# 1. Prepare SQL data in memory

FACT_TABLE = "quake_events"

print("preparing data...")

engine = create_engine('sqlite:///data.sqlite')
if sys.argv[2] != "0":
    create_flag = True
else:
    create_flag = False
create_table_from_csv(engine,
                      sys.argv[1],
                      table_name=FACT_TABLE,
                      fields=[
                                ("EventID","integer"),
                                ("EventType","string"),
                                ("RegionType","string"),
                                ("Region","string"),
                                ("Fulltime","string"),
                                ("Date","date"),
                                ("Year","integer"),
                                ("Month","integer"),
                                ("Day","integer"),
                                ("Time","date"),
                                ("Latitude","float"),
                                ("Longitude","float"),
                                ("Depth","float"),
                                ("Magnitude","float"),
                                ("MagnitudeUnit","string")],
                     create_id=True,
                     create_table=create_flag
                  )

print("done. file data.sqlite created")
