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

        DSS_OUTPUT_FILE = os.path.join(run_date, run_name, '2008_2_Events/2008_2_Events_run.dss')
        # Default run for current day

        myDss = HecDss.open(DSS_OUTPUT_FILE)
        output_file_dir = os.path.join(run_date, run_name,'output')
        DISCHARGE_CSV_FILE_PATH = os.path.join(output_file_dir,'DailyDischarge.csv')
        if not os.path.exists(output_file_dir):
            os.makedirs(output_file_dir)
        print 'Open Discharge CSV ::', DISCHARGE_CSV_FILE_PATH
        csvWriter = csv.writer(open(DISCHARGE_CSV_FILE_PATH, 'w'), delimiter=',', quotechar='|')

        flow = myDss.get('//HANWELLA/FLOW//1HOUR/RUN:RUN 1/', 1)

        if flow.numberValues == 0:
            MessageBox.showError('No Data', 'Error')
        else:
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
