#!/usr/bin/python

# Rainfall CSV file format should follow as
# https://publicwiki.deltares.nl/display/FEWSDOC/CSV

import java, csv, sys, datetime, os
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

        CONFIG = json.loads(open('/home/uwcc-admin/udp_150/HecHms/config.json').read())
        # print('Config :: ', CONFIG)

        NUM_METADATA_LINES = 0;
        HEC_HMS_MODEL_DIR = './2008_2_Events'
        DSS_INPUT_FILE = './2008_2_Events/2008_2_Events_force.dss'
        RAIN_CSV_FILE = 'DailyRain.csv'
        RAIN_FALL_DIR = '/HecHms/RainFall'

        if 'HEC_HMS_MODEL_DIR' in CONFIG:
            HEC_HMS_MODEL_DIR = CONFIG['HEC_HMS_MODEL_DIR']
        if 'DSS_INPUT_FILE' in CONFIG:
            DSS_INPUT_FILE = CONFIG['DSS_INPUT_FILE']
        if 'RAIN_CSV_FILE' in CONFIG:
            RAIN_CSV_FILE = CONFIG['RAIN_CSV_FILE']
        if 'RAIN_FALL_DIR' in CONFIG:
            RAIN_FALL_DIR = CONFIG['RAIN_FALL_DIR']

        date = ''
        time = ''

        # Passing Commandline Options to Jython. Not same as getopt in python.
        # Ref: http://www.jython.org/jythonbook/en/1.0/Scripting.html#parsing-commandline-options
        # Doc : https://docs.python.org/2/library/optparse.html
        parser = OptionParser(description='Upload CSV data into HEC-HMS DSS storage')
        # ERROR: Unable to use `-d` or `-D` option with OptionParser
        parser.add_option("--date", help="Date in YYYY-MM. Default is current date.")
        parser.add_option("--time", help="Time in HH:MM:SS. Default is current time.")
        parser.add_option("--hec-hms-model-dir",
                          help="Path of HEC_HMS_MODEL_DIR directory. Otherwise using the `HEC_HMS_MODEL_DIR` from CONFIG.json")

        (options, args) = parser.parse_args()
        print
        'Commandline Options:', options

        if options.date:
            date = options.date
        if options.time:
            time = options.time
        # if options.hec_hms_model_dir:
        #     HEC_HMS_MODEL_DIR = options.hec_hms_model_dir
        #     # Reconstruct DSS_INPUT_FILE path
        #     dssFileName = DSS_INPUT_FILE.rsplit('/', 1)
        #     DSS_INPUT_FILE = os.path.join(HEC_HMS_MODEL_DIR, dssFileName[-1])
        #
        # # Replace CONFIG.json variables
        # if re.match('^\$\{(HEC_HMS_MODEL_DIR)\}', DSS_INPUT_FILE):
        #     DSS_INPUT_FILE = re.sub('^\$\{(HEC_HMS_MODEL_DIR)\}', '', DSS_INPUT_FILE).strip("/\\")
        #     DSS_INPUT_FILE = os.path.join(HEC_HMS_MODEL_DIR, DSS_INPUT_FILE)
        #     print
        #     '"Set DSS_INPUT_FILE=', DSS_INPUT_FILE

        # Default run for current day
        modelState = datetime.datetime.now()
        if date:
            modelState = datetime.datetime.strptime(date, '%Y-%m-%d')
        date = modelState.strftime("%Y-%m-%d")
        if time:
            modelState = datetime.datetime.strptime('%s %s' % (date, time), '%Y-%m-%d %H:%M:%S')
        time = modelState.strftime("%H:%M:%S")

        myDss = HecDss.open(DSS_INPUT_FILE)

        output_file_dir = os.path.join(RAIN_FALL_DIR, modelState.strftime("%Y-%m-%d_%H:%M:%S"))
        if not os.path.exists(output_file_dir):
            os.makedirs(output_file_dir)
        RAIN_CSV_FILE_PATH = os.path.join(output_file_dir, RAIN_CSV_FILE)
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