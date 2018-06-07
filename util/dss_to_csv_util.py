#!/usr/bin/python

import java, csv, sys, datetime, os, re

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

        CONFIG = json.loads(open('CONFIG.json').read())
        # print('Config :: ', CONFIG)

        NUM_METADATA_LINES = 2;
        HEC_HMS_MODEL_DIR = './2008_2_Events'
        DSS_OUTPUT_FILE = './2008_2_Events/2008_2_Events.dss'
        DISCHARGE_CSV_FILE = 'DailyDischarge.csv'
        OUTPUT_DIR = './OUTPUT'

        if 'HEC_HMS_MODEL_DIR' in CONFIG:
            HEC_HMS_MODEL_DIR = CONFIG['HEC_HMS_MODEL_DIR']
        if 'DSS_OUTPUT_FILE' in CONFIG:
            DSS_OUTPUT_FILE = CONFIG['DSS_OUTPUT_FILE']
        if 'DISCHARGE_CSV_FILE' in CONFIG:
            DISCHARGE_CSV_FILE = CONFIG['DISCHARGE_CSV_FILE']
        if 'OUTPUT_DIR' in CONFIG:
            OUTPUT_DIR = CONFIG['OUTPUT_DIR']

        date = ''
        time = ''
        startDateTS = ''
        startTimeTS = ''
        tag = ''

        # Passing Commandline Options to Jython. Not same as getopt in python.
        # Ref: http://www.jython.org/jythonbook/en/1.0/Scripting.html#parsing-commandline-options
        # Doc : https://docs.python.org/2/library/optparse.html
        parser = OptionParser(description='Upload CSV data into HEC-HMS DSS storage')
        # ERROR: Unable to use `-d` or `-D` option with OptionParser
        parser.add_option("--date", help="Date in YYYY-MM. Default is current date.")
        parser.add_option("--time", help="Time in HH:MM:SS. Default is current time.")
        parser.add_option("--start-date",
                          help="Start date of timeseries which need to run the forecast in YYYY-MM-DD format. Default is same as -d(date).")
        parser.add_option("--start-time",
                          help="Start time of timeseries which need to run the forecast in HH:MM:SS format. Default is same as -t(date).")
        parser.add_option("-T", "--tag", help="Tag to differential simultaneous Forecast Runs E.g. wrf1, wrf2 ...")
        parser.add_option("--hec-hms-model-dir",
                          help="Path of HEC_HMS_MODEL_DIR directory. Otherwise using the `HEC_HMS_MODEL_DIR` from CONFIG.json")

        (options, args) = parser.parse_args()
        print
        'Commandline Options:', options

        if options.date:
            date = options.date
        if options.time:
            time = options.time
        if options.start_date:
            startDateTS = options.start_date
        if options.start_time:
            startTimeTS = options.start_time
        if options.tag:
            tag = options.tag
        if options.hec_hms_model_dir:
            HEC_HMS_MODEL_DIR = options.hec_hms_model_dir
            # Reconstruct DSS_OUTPUT_FILE path
            dssFileName = DSS_OUTPUT_FILE.rsplit('/', 1)
            DSS_OUTPUT_FILE = os.path.join(HEC_HMS_MODEL_DIR, dssFileName[-1])

        # Replace CONFIG.json variables
        if re.match('^\$\{(HEC_HMS_MODEL_DIR)\}', DSS_OUTPUT_FILE):
            DSS_OUTPUT_FILE = re.sub('^\$\{(HEC_HMS_MODEL_DIR)\}', '', DSS_OUTPUT_FILE).strip("/\\")
            DSS_OUTPUT_FILE = os.path.join(HEC_HMS_MODEL_DIR, DSS_OUTPUT_FILE)
            print
            '"Set DSS_OUTPUT_FILE=', DSS_OUTPUT_FILE

        # Default run for current day
        modelState = datetime.datetime.now()
        if date:
            modelState = datetime.datetime.strptime(date, '%Y-%m-%d')
        date = modelState.strftime("%Y-%m-%d")
        if time:
            modelState = datetime.datetime.strptime('%s %s' % (date, time), '%Y-%m-%d %H:%M:%S')
        time = modelState.strftime("%H:%M:%S")

        startDateTimeTS = datetime.datetime.now()
        if startDateTS:
            startDateTimeTS = datetime.datetime.strptime(startDateTS, '%Y-%m-%d')
        else:
            startDateTimeTS = datetime.datetime.strptime(date, '%Y-%m-%d')
        startDateTS = startDateTimeTS.strftime("%Y-%m-%d")

        if startTimeTS:
            startDateTimeTS = datetime.datetime.strptime('%s %s' % (startDateTS, startTimeTS), '%Y-%m-%d %H:%M:%S')
        startTimeTS = startDateTimeTS.strftime("%H:%M:%S")

        print
        'Start DSSTOCSV.py on ', date, '@', time, tag, HEC_HMS_MODEL_DIR
        print
        ' With Custom starting', startDateTS, '@', startTimeTS

        myDss = HecDss.open(DSS_OUTPUT_FILE)
        fileName = DISCHARGE_CSV_FILE.rsplit('.', 1)
        # str .format not working on this version
        fileName = '%s-%s%s.%s' % (fileName[0], date, '.' + tag if tag else '', fileName[1])
        DISCHARGE_CSV_FILE_PATH = os.path.join(OUTPUT_DIR, fileName)
        print
        'Open Discharge CSV ::', DISCHARGE_CSV_FILE_PATH
        csvWriter = csv.writer(open(DISCHARGE_CSV_FILE_PATH, 'w'), delimiter=',', quotechar='|')

        flow = myDss.get('//HANWELLA/FLOW//1HOUR/RUN:RUN 1/', 1)

        if flow.numberValues == 0:
            MessageBox.showError('No Data', 'Error')
        else:
            csvWriter.writerow(['Location Ids', 'Hanwella'])
            csvWriter.writerow(['Time', 'Flow'])

            print
            flow.values[:1], flow.times[:1]
            print
            flow.values[-1], flow.times[-1]

            csvList = []

            for i in range(0, flow.numberValues):
                # print int(flow.times[i])
                time = HecTime()
                time.set(int(flow.times[i]))

                d = [time.year(), '%d' % (time.month(),), '%d' % (time.day(),)]
                t = ['%d' % (time.hour(),), '%d' % (time.minute(),), '%d' % (time.second(),)]
                if (int(t[0]) > 23):
                    t[0] = '23'
                    dtStr = '-'.join(str(x) for x in d) + ' ' + ':'.join(str(x) for x in t)
                    dt = datetime.datetime.strptime(dtStr, '%Y-%m-%d %H:%M:%S')
                    dt = dt + datetime.timedelta(hours=1)
                else:
                    dtStr = '-'.join(str(x) for x in d) + ' ' + ':'.join(str(x) for x in t)
                    dt = datetime.datetime.strptime(dtStr, '%Y-%m-%d %H:%M:%S')

                csvList.append([dt.strftime('%Y-%m-%d %H:%M:%S'), "%.2f" % flow.values[i]])

            print
            csvList[:3], "...", csvList[-3:]
            csvWriter.writerows(csvList)

    except Exception, e:
        MessageBox.showError(' '.join(e.args), "Python Error")
    except java.lang.Exception, e:
        MessageBox.showError(e.getMessage(), "Error")
finally:
    myDss.done()
    print
    '\nCompleted converting.'
