#!/usr/bin/python

# Rainfall CSV file format should follow as
# https://publicwiki.deltares.nl/display/FEWSDOC/CSV

import java, csv, sys, os
from hec.script import MessageBox
from hec.heclib.dss import HecDss
from hec.heclib.util import HecTime
from hec.io import TimeSeriesContainer

from optparse import OptionParser

sys.path.append("./simplejson-2.5.2")
import simplejson as json

try:
    try:
        print
        'Jython version: ', sys.version

        date = ''
        time = ''
        NUM_METADATA_LINES = 0
        # Passing Commandline Options to Jython. Not same as getopt in python.
        # Ref: http://www.jython.org/jythonbook/en/1.0/Scripting.html#parsing-commandline-options
        # Doc : https://docs.python.org/2/library/optparse.html
        parser = OptionParser(description='Upload CSV data into HEC-HMS DSS storage')
        # ERROR: Unable to use `-d` or `-D` option with OptionParser
        parser.add_option("--date", help="Date in YYYY-MM. Default is current date.")
        parser.add_option("--run_name", help="Time in HH:MM:SS. Default is current time.")
        parser.add_option("--model_dir",
                          help="Path of HEC_HMS_MODEL_DIR directory. Otherwise using the `HEC_HMS_MODEL_DIR` from CONFIG.json")

        (options, args) = parser.parse_args()
        print
        'Commandline Options:', options

        if options.date:
            run_date = options.date
        if options.run_name:
            run_name = options.run_name
        if options.model_dir:
            HEC_HMS_MODEL_DIR = options.model_dir

        DSS_INPUT_FILE = os.path.join(run_date, run_name, 'model/2008_2_Events_input.dss')
        myDss = HecDss.open(DSS_INPUT_FILE)

        RAIN_CSV_FILE_PATH = os.path.join(run_date, run_name, 'input/DailyRain.csv')
        print
        'Open Rainfall CSV ::', RAIN_CSV_FILE_PATH
        csvReader = csv.reader(open(RAIN_CSV_FILE_PATH, 'r'), delimiter=',', quotechar='|')
        csvList = list(csvReader)
        numLocationList = ['Location Names','Awissawella','Colombo']
        numLocations = len(numLocationList) - 1
        numValues = len(csvList)  # Ignore Metadata
        locationIds = ['Awissawella','Colombo']
        print
        'Start reading', numLocations, csvList[0][0], ':', ', '.join(csvList[0][1:])
        print
        'Period of ', numValues, 'values'
        print
        'Location Ids :', locationIds

        for i in range(0, numLocations):
            print '\n>>>>>>> Start processing ', locationIds[i], '<<<<<<<<<<<<'
            precipitations = []
            for j in range(NUM_METADATA_LINES, numValues + NUM_METADATA_LINES):
                p = float(csvList[j][i + 1])
                precipitations.append(p)

            print 'Precipitation of ', locationIds[i], precipitations[:10]
            tsc = TimeSeriesContainer()
            # tsc.fullName = "/BASIN/LOC/FLOW//1HOUR/OBS/"
            # tsc.fullName = '//' + locationIds[i].upper() + '/PRECIP-INC//1DAY/GAGE/'
            tsc.fullName = '//' + locationIds[i].upper() + '/PRECIP-INC//1HOUR/GAGE/'

            print 'Start time : ', csvList[NUM_METADATA_LINES][0]
            start = HecTime(csvList[NUM_METADATA_LINES][0])
            tsc.interval = 60  # in minutes
            times = []
            for value in precipitations:
                times.append(start.value())
                start.add(tsc.interval)
            tsc.times = times
            tsc.values = precipitations
            tsc.numberValues = len(precipitations)
            tsc.units = "MM"
            tsc.type = "PER-CUM"
            myDss.put(tsc)

    except Exception, e:
        MessageBox.showError(' '.join(e.args), "Python Error")
    except java.lang.Exception, e:
        MessageBox.showError(e.getMessage(), "Error")
finally:
    myDss.done()
    print
    '\nCompleted converting ', RAIN_CSV_FILE_PATH, ' to ', DSS_INPUT_FILE
    print
    'done'