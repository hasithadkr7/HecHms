import collections
import datetime
import getopt
import json
import os
import re
import sys
import traceback
import pandas as pd


DSSDateTime = collections.namedtuple('DSSDateTime', ['dateTime', 'date', 'time'])


def usage():
    usage_text = """
Usage: ./Update_HECHMS.py [-d date] [-h -i] [-s sInterval] [-c cInterval] 

-h  --help          Show usage
-d  --date          Model State Date in YYYY-MM. Default is current date.
-t  --time          Model State Time in HH:MM:SS. Default is current time.
-f  --forward       Go to number of days front.
-b  --backward      Go to back number of days.
    --hec-hms-model-dir Path of HEC_HMS_MODEL_DIR directory. 
                        Otherwise using the `HEC_HMS_MODEL_DIR` from CONFIG.json
"""
    print(usage_text)


def get_dss_date_time(date_time):
    # Removed DSS formatting with HEC-HMS upgrading from 3.5 to 4.1
    my_date = date_time.strftime('%d %B %Y')
    my_time = date_time.strftime('%H:%M')
    return DSSDateTime(
        dateTime=my_date + ' ' + my_time,
        date=my_date,
        time=my_time
    )


def update_model_script(model_dir, model_name):
    script_file_path = os.path.join(model_dir, model_name+'.script')
    script_file = open(script_file_path, 'w')
    script_file.write('from hms.model.JythonHms import *\r\n')
    script_file.write('OpenProject("{}", "{}")\r\n'.format(model_name, model_dir))
    script_file.write('Compute("Run 1")\r\n')
    script_file.write('Exit(1)\r\n')
    script_file.close()


def update_model_configs(control_file, run_file, gage_file, rainfall_file, init_state=False, backward=2, forward=3):
    try:
        HEC_HMS_CONTROL = control_file
        HEC_HMS_RUN = run_file
        HEC_HMS_GAGE = gage_file
        TIME_INTERVAL = 60  # In minutes
        STATE_INTERVAL = 1 * 24 * 60  # In minutes (1 day)
        CONTROL_INTERVAL = 8 * 24 * 60  # In minutes (8 day)

        #model_date_time = datetime.datetime.strptime('%s %s' % (date, time), '%Y-%m-%d %H:%M:%S')

        print('Update_HECHMS startTime:', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        rainfall_df = pd.read_csv(rainfall_file)
        startDateTime = datetime.datetime.strptime(rainfall_df.values[0].tolist()[0], '%Y-%m-%d %H:%M:%S')
        endDateTime = datetime.datetime.strptime(rainfall_df.values[-1].tolist()[0], '%Y-%m-%d %H:%M:%S')
        #startDateTime = model_date_time - datetime.timedelta(hours=(backward*24)+1)
        #startDateTime = startDateTime.strftime("%Y-%m-%d %H:%M:%S")
        #endDateTime = model_date_time + datetime.timedelta(hours=(forward*24) - 1)
        #endDateTime = endDateTime.strftime("%Y-%m-%d %H:%M:%S")
        print("--------------------startDateTime : ", startDateTime)
        print("--------------------endDateTime : ", endDateTime)
        startDateTimeDSS = get_dss_date_time(startDateTime)
        endDateTimeDSS = get_dss_date_time(endDateTime)
        startDate = startDateTimeDSS.date
        startTime = startDateTimeDSS.time
        endDate = endDateTimeDSS.date
        endTime = endDateTimeDSS.time

        # TODO : Increase Control Interval with gap between startDateTimeTS and modelState
        controlEndDateTime = startDateTime + datetime.timedelta(minutes=CONTROL_INTERVAL)
        controlEndDateTimeDSS = get_dss_date_time(controlEndDateTime)
        controlEndDate = controlEndDateTimeDSS.date
        controlEndTime = controlEndDateTimeDSS.time

        #############################################
        # Update Control file                       #
        #############################################
        controlFile = open(HEC_HMS_CONTROL, 'r')
        controlData = controlFile.readlines()
        controlFile.close()

        controlFile = open(HEC_HMS_CONTROL, 'w')
        for line in controlData:
            if 'Start Date:' in line:
                s = line[:line.rfind('Start Date:')+11]
                s += ' ' + startDate
                controlFile.write(s + '\n')
            elif 'Start Time:' in line:
                s = line[:line.rfind('Start Time:')+11]
                s += ' ' + startTime
                controlFile.write(s + '\n')
            elif 'End Date:' in line:
                s = line[:line.rfind('End Date:')+9]
                s += ' ' + controlEndDate
                controlFile.write(s + '\n')
            elif 'End Time:' in line:
                s = line[:line.rfind('End Time:')+9]
                s += ' ' + controlEndTime
                controlFile.write(s + '\n')
            elif 'Time Interval:' in line:
                s = line[:line.rfind('Time Interval:')+14]
                s += ' ' + str(TIME_INTERVAL)
                controlFile.write(s + '\n')
            else:
                controlFile.write(line)

        #############################################
        # Update Run file                           #
        #############################################
        runFile = open(HEC_HMS_RUN, 'r')
        runData = runFile.readlines()
        runFile.close()

        runFile = open(HEC_HMS_RUN, 'w')
        for line in runData:
            if 'Control:' in line:
                runFile.write(line)
                indent = line[:line.rfind('Control:')]

                # TODO: Handle for Hour mode
                saveStateDateTime = startDateTime + datetime.timedelta(minutes=STATE_INTERVAL)
                saveStateDateTimeDSS = get_dss_date_time(saveStateDateTime)
                startStateDateTime = startDateTime - datetime.timedelta(minutes=STATE_INTERVAL)
                line1 = indent + 'Save State Name: State_' + startDateTime.strftime('%Y_%m_%d') + '_To_' + saveStateDateTime.strftime('%Y_%m_%d')
                line2 = indent + 'Save State Date: ' + saveStateDateTimeDSS.date
                line3 = indent + 'Save State Time: ' + saveStateDateTimeDSS.time
                runFile.write(line1 + '\n'); runFile.write(line2 + '\n'); runFile.write(line3 + '\n')
                if not init_state:
                    line4 = indent + 'Start State Name: State_' + startStateDateTime.strftime('%Y_%m_%d') + '_To_' + startDateTime.strftime('%Y_%m_%d')
                    runFile.write(line4 + '\n')

            # Skip Writing these lines
            elif 'Save State At End of Run:' in line:
                continue
            elif 'Save State Name:' in line:
                continue
            elif 'Save State Date:' in line:
                continue
            elif 'Save State Time:' in line:
                continue
            elif 'Start State Name:' in line:
                continue
            else :
                runFile.write(line)

        #############################################
        # Update Gage file                          #
        #############################################
        gageFile = open(HEC_HMS_GAGE, 'r')
        gageData = gageFile.readlines()
        gageFile.close()

        gageFile = open(HEC_HMS_GAGE, 'w')
        for line in gageData:
            if 'Start Time:' in line:
                s = line[:line.rfind('Start Time:')+11]
                s += ' ' + startDate + ', ' + startTime
                gageFile.write(s + '\n')
            elif 'End Time:' in line:
                s = line[:line.rfind('End Time:')+9]
                s += ' ' + endDate + ', ' + endTime
                gageFile.write(s + '\n')
            else:
                gageFile.write(line)


    except Exception as e:
        traceback.print_exc()
        print(e)
    finally:
        controlFile.close()
        print('Updated HEC-HMS Control file ')
