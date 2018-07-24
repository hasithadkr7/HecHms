#!/usr/bin/python3

import csv
import datetime
import getopt
import json
import os
import sys
import traceback
import pandas as pd
from db_util import MySqlAdapter, get_type_by_date, get_event_id, create_event_id


def usage():
    usageText = """
Usage: ./CSVTODAT.py [-d YYYY-MM-DD] [-h]

-h  --help          Show usage
-d  --date          Model State Date in YYYY-MM. Default is current date.
-t  --time          Model State Time in HH:MM:SS. Default is current time.
    --start-date    Start date of timeseries which need to run the forecast in YYYY-MM-DD format. Default is same as -d(date).
    --start-time    Start time of timeseries which need to run the forecast in HH:MM:SS format. Default is same as -t(date).
-T  --tag           Tag to differential simultaneous Forecast Runs E.g. wrf1, wrf2 ...
-f  --forceInsert   Force Insert into the database. May override existing values.
-n  --name          Name field value of the Run table in Database. Use time format such as 'Cloud-1-<%H:%M:%S>' to replace with time(t).
"""
    print(usageText)


def extract_forecast_timeseries(timeseries, extract_date, extract_time, by_day=False):
    """
    Extracted timeseries upward from given date and time
    E.g. Consider timeseries 2017-09-01 to 2017-09-03
    date: 2017-09-01 and time: 14:00:00 will extract a timeseries which contains
    values that timestamp onwards
    """
    print('LibForecastTimeseries:: extractForecastTimeseries')
    if by_day:
        extract_date_time = datetime.strptime(extract_date, '%Y-%m-%d')
    else:
        extract_date_time = datetime.strptime('%s %s' % (extract_date, extract_time), '%Y-%m-%d %H:%M:%S')

    is_date_time = isinstance(timeseries[0][0], datetime)
    new_timeseries = []
    for i, tt in enumerate(timeseries):
        tt_date_time = tt[0] if is_date_time else datetime.strptime(tt[0], '%Y-%m-%d %H:%M:%S')
        if tt_date_time >= extract_date_time:
            new_timeseries = timeseries[i:]
            break
    return new_timeseries


def extract_forecast_timeseries_in_days(timeseries):
    """
    Devide into multiple timeseries for each day
    E.g. Consider timeseries 2017-09-01 14:00:00 to 2017-09-03 23:00:00
    will devide into 3 timeseries with
    [
        [2017-09-01 14:00:00-2017-09-01 23:00:00],
        [2017-09-02 14:00:00-2017-09-02 23:00:00],
        [2017-09-03 14:00:00-2017-09-03 23:00:00]
    ]
    """
    new_timeseries = []
    if len(timeseries) > 0:
        group_timeseries = []
        is_date_time_obs = isinstance(timeseries[0][0], datetime)
        prev_date = timeseries[0][0] if is_date_time_obs else datetime.strptime(timeseries[0][0], '%Y-%m-%d %H:%M:%S')
        prev_date = prev_date.replace(hour=0, minute=0, second=0, microsecond=0)
        for tt in timeseries:
            # Match Daily
            tt_date_time = tt[0] if is_date_time_obs else datetime.strptime(tt[0], '%Y-%m-%d %H:%M:%S')
            if prev_date == tt_date_time.replace(hour=0, minute=0, second=0, microsecond=0):
                group_timeseries.append(tt)
            else:
                new_timeseries.append(group_timeseries[:])
                group_timeseries = []
                prev_date = tt_date_time.replace(hour=0, minute=0, second=0, microsecond=0)
                group_timeseries.append(tt)

    return new_timeseries


def save_forecast_timeseries(adapter, time_series_data, model_date_time, opts):
    print('CSVTODAT:: save_forecast_timeseries:: len', len(time_series_data), model_date_time)
    req_date = datetime.datetime.strptime(model_date_time.strftime("%Y-%m-%d"), '%Y-%m-%d')
    df = pd.pivot_table(time_series_data, columns=time_series_data['time'].str[:10])
    days_list = df.columns.values
    for day in days_list:
        type = get_type_by_date(req_date, day)
        sub_df = time_series_data.loc[time_series_data['time'].str[:10] == day]
        if type != 'Error':
            meta_data = {
                'station': 'Hanwella',
                'variable': 'Discharge',
                'unit': 'm3/s',
                'type': type,
                'source': 'HEC-HMS',
                'name': opts.get('run_name', 'Cloud-1'),
            }
            event_id = get_event_id(adapter, meta_data)
            if event_id is None:
                event_id = create_event_id(adapter, meta_data)
            size = sub_df.shape[0]

            def get_event_column(event_id, size, event_list=[]):
                for i in range(0, size):
                    event_list.append(event_id)
                return event_list

            if size > 0:
                sub_df.insert(loc=0, column='id', value=get_event_column(event_id, size))
                print(sub_df)


def upload_data_to_db(run_datetime, discharge_file, run_name, force_insert=False):
    try:
        CSV_NUM_METADATA_LINES = 2
        DAT_WIDTH = 12
        DISCHARGE_CSV_FILE = 'DailyDischarge.csv'

        forceInsert = force_insert
        runName = run_name

        print('Open Discharge CSV ::', discharge_file)
        time_series_data = pd.read_csv(discharge_file, names=['time', 'value'])

        # Validate Discharge Timeseries
        if not time_series_data.shape[0] > 0:
            print('ERROR: Discharge timeseries length is zero.')
            sys.exit(1)

        # Save Forecast values into Database
        opts = {
            'forceInsert': forceInsert,
            'runName': runName
        }
        save_forecast_timeseries(MySqlAdapter(), time_series_data, run_datetime, opts)

    except Exception as e:
        print(e)
        traceback.print_exc()
