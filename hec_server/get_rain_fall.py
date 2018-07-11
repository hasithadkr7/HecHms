import datetime
import getopt
import json
import pandas as pd
import os
import sys
import csv
from decimal import *
from db_util import MySqlAdapter, get_time_series_values


def usage():
    usage_text = """
Usage: ./get_rain_fall.py [-d YYYY-MM-DD] [-t HH:MM:SS] [-h]

-h  --help          Show usage
-d  --date          Date in YYYY-MM-DD. Default is current date.
-t  --time          Time in HH:MM:SS. Default is current time.
-p  --path          Output directory path
-f  --forward       Days to future (Int)
-b  --backward      Days to past (Int)
"""
    print(usage_text)


def get_timeseries(my_adapter, my_event_id, my_opts):
    existing_timeseries = my_adapter.retrieve_timeseries([my_event_id], my_opts)
    new_timeseries = []
    if len(existing_timeseries) > 0 and len(existing_timeseries[0]['timeseries']) > 0:
        existing_timeseries = existing_timeseries[0]['timeseries']
        prev_date_time = existing_timeseries[0][0]
        prev_sum = existing_timeseries[0][1]
        for tt in existing_timeseries:
            tt[0] = tt[0]
            if prev_date_time.replace(minute=0, second=0, microsecond=0) == tt[0].replace(minute=0, second=0,
                                                                                          microsecond=0):
                prev_sum += tt[1]  # TODO: If missing or minus -> ignore
                # TODO: Handle End of List
            else:
                new_timeseries.append([tt[0].replace(minute=0, second=0, microsecond=0), prev_sum])
                prev_date_time = tt[0]
                prev_sum = tt[1]
    return new_timeseries


def get_forecasted_timeseries1(my_adapter, model_date_time, forecasted_id0, forecasted_id1,
                               forecasted_id2):  # eg: 2018-05-22 21:00:00
    forecast_d0_start = model_date_time - datetime.timedelta(hours=48)
    forecast_d0_end = model_date_time + datetime.timedelta(hours=0)
    forecast_d0_end = forecast_d0_end.strftime("%Y-%m-%d 23:00:00")
    forecast_d0_opts = {
        'from': forecast_d0_start.strftime("%Y-%m-%d %H:%M:%S"),
        'to': forecast_d0_end
    }
    forecast_d0_timeseries = get_timeseries(my_adapter, forecasted_id0, forecast_d0_opts)

    forecast_d1_start = datetime.datetime.strptime(forecast_d0_end, '%Y-%m-%d %H:%M:%S')
    forecast_d1_end = datetime.datetime.strptime(forecast_d0_end, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=24)
    forecast_d1_opts = {
        'from': forecast_d1_start.strftime("%Y-%m-%d %H:%M:%S"),
        'to': forecast_d1_end.strftime("%Y-%m-%d %H:%M:%S")
    }
    forecast_d1_timeseries = get_timeseries(my_adapter, forecasted_id1, forecast_d1_opts)
    forecast_d2_start = forecast_d1_end
    forecast_d2_end = forecast_d1_end + datetime.timedelta(hours=24)
    forecast_d2_opts = {
        'from': forecast_d2_start.strftime("%Y-%m-%d %H:%M:%S"),
        'to': forecast_d2_end.strftime("%Y-%m-%d %H:%M:%S")
    }
    forecast_d2_timeseries = get_timeseries(my_adapter, forecasted_id2, forecast_d2_opts)
    forecasted_timeseries = forecast_d0_timeseries + forecast_d1_timeseries + forecast_d2_timeseries

    forecast_end_time = model_date_time + datetime.timedelta(hours=72)
    print("forecast_end_time: ", forecast_end_time)
    last_avaialble_forecast_time = forecasted_timeseries[-1][0]

    print("last_avaialble_forecast_time : ", last_avaialble_forecast_time)
    print("last_avaialble_forecast_time type : ", type(last_avaialble_forecast_time))

    print("forecast_end_time : ", forecast_end_time)
    print("forecast_end_time type : ", type(forecast_end_time))

    while forecast_end_time > last_avaialble_forecast_time:
        next_forecast_time = last_avaialble_forecast_time + datetime.timedelta(hours=1)
        forecasted_timeseries.append([next_forecast_time, Decimal('0.0')])
        last_avaialble_forecast_time = next_forecast_time
    print("length forecasted_timeseries : ", len(forecasted_timeseries))
    print("forecasted_timeseries: ", forecasted_timeseries)

    return forecasted_timeseries


def get_forecasted_timeseries(adapter, model_date_time, forecasted_id0, forecasted_id1,
                              forecasted_id2):  # eg: 2018-05-22 21:00:00
    forecast_d0_start = model_date_time - datetime.timedelta(hours=48,minutes=90)
    forecast_d0_end = model_date_time + datetime.timedelta(hours=0)
    forecast_d0_end = forecast_d0_end.strftime("%Y-%m-%d 23:00:00")
    forecast_d0_timeseries = get_time_series_values(adapter, forecasted_id0,
                                                    forecast_d0_start.strftime("%Y-%m-%d %H:%M:%S"), forecast_d0_end)
    # print("forecast_d0_timeseries : ", forecast_d0_timeseries)

    forecast_d1_start = datetime.datetime.strptime(forecast_d0_end, '%Y-%m-%d %H:%M:%S')
    forecast_d1_end = datetime.datetime.strptime(forecast_d0_end, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=24)
    forecast_d1_timeseries = get_time_series_values(adapter, forecasted_id1,
                                                    forecast_d1_start.strftime("%Y-%m-%d %H:%M:%S"),
                                                    forecast_d1_end.strftime("%Y-%m-%d %H:%M:%S"))
    # print("forecast_d1_timeseries : ", forecast_d1_timeseries)

    forecast_d2_start = forecast_d1_end
    forecast_d2_end = forecast_d1_end + datetime.timedelta(hours=24)
    forecast_d2_timeseries = get_time_series_values(adapter, forecasted_id2,
                                                    forecast_d2_start.strftime("%Y-%m-%d %H:%M:%S"),
                                                    forecast_d2_end.strftime("%Y-%m-%d %H:%M:%S"))
    # print("forecast_d2_timeseries : ", forecast_d2_timeseries)

    # forecasted_timeseries = (forecast_d0_timeseries - forecast_d1_timeseries).combine_first(forecast_d0_timeseries)
    # forecasted_timeseries = (forecasted_timeseries - forecast_d2_timeseries).combine_first(forecasted_timeseries)

    forecasted_timeseries = pd.merge_ordered(forecast_d0_timeseries, forecast_d1_timeseries, how='outer')
    forecasted_timeseries = pd.merge_ordered(forecasted_timeseries, forecast_d2_timeseries, how='outer')
    grouped = forecasted_timeseries.groupby('time')
    index = [gp_keys[0] for gp_keys in grouped.groups.values()]
    new_forecasted_timeseries = forecasted_timeseries.reindex(index)
    # print("new_forecasted_timeseries : ", new_forecasted_timeseries)

    return new_forecasted_timeseries


def get_observed_timeseries(adapter, model_date_time, observed_id, backward):
    observed_start = model_date_time - datetime.timedelta(hours=backward*24, minutes=90)
    observed_end = model_date_time
    observed_timeseries = get_time_series_values(adapter, observed_id, observed_start.strftime("%Y-%m-%d %H:%M:%S"),
                                                 observed_end.strftime("%Y-%m-%d %H:%M:%S"))
    return observed_timeseries


def get_kub_mean_timeseries(my_adapter, model_date_time, observed_id, forecasted_id0, forecasted_id1, forecasted_id2, backward):
    observed_timeseries = get_observed_timeseries(my_adapter, model_date_time, observed_id, backward)
    forecasted_timeseries = get_forecasted_timeseries(my_adapter, model_date_time, forecasted_id0, forecasted_id1,
                                                      forecasted_id2)

    forecasted_timeseries = pd.merge_ordered(observed_timeseries, forecasted_timeseries, how='outer')
    grouped = forecasted_timeseries.groupby('time')
    index = [gp_keys[0] for gp_keys in grouped.groups.values()]
    new_forecasted_timeseries = forecasted_timeseries.reindex(index)
    return new_forecasted_timeseries.sort_values('time')


# Currently we don't have KLB obeserved values
def get_klb_mean_timeseries(my_adapter, model_date_time, forecasted_id0, forecasted_id1, forecasted_id2, backward):
    forecasted_timeseries = get_forecasted_timeseries(my_adapter, model_date_time, forecasted_id0, forecasted_id1,
                                                      forecasted_id2)
    newforecasted_timeseries = forecasted_timeseries.sort_values('time')
    # print("get_klb_mean_timeseries|newforecasted_timeseries : ", newforecasted_timeseries)
    return newforecasted_timeseries


def generate_rf_file(rf_fall_dir, data_date, data_time, backward=2, forward=3):
    try:
        RAIN_FALL_DIR = rf_fall_dir
        RAIN_CSV_FILE = 'DailyRain.csv'
        # Kelani Upper Basin
        kub_observed_id = 'b0e008522be904bcf71e290b3b0096b33c3e24d9b623dcbe7e58e7d1cc82d0db'
        kub_forecasted_id0 = 'fb575cb25f1e3d3a07c84513ea6a91c8f2fb98454df1a432518ab98ad7182861'  # wrf0, kub_mean, 0-d
        kub_forecasted_id1 = '9b18ffa16b251319ad1a931c4e1011b4ce42c874543def69b8a4af76d7b8f9fc'  # wrf0, kub_mean, 1-d
        kub_forecasted_id2 = 'e0e9cdc2aa4fef7178af08b987f4febc186d19397be744525fb6263815ca5fef'  # wrf0, kub_mean, 2-d
        # Kelani Lower Basin
        klb_observed_id = '69c464f749b36d9e55e461947238e7ed809c2033e75ae56234f466eec00aee35'  # wrf0, klb_mean, 0-d
        klb_forecasted_id0 = '69c464f749b36d9e55e461947238e7ed809c2033e75ae56234f466eec00aee35'  # wrf0, kub_mean, 0-d
        klb_forecasted_id1 = '35599583ae45d2c0ff93485b8a444da19fabdda8bf8fb539a6d77a0b0819da0a'  # wrf0, kub_mean, 1-d
        klb_forecasted_id2 = 'c48dbb9475ec31b3419bd3dd4206fdff3c53d4d156fa5681ccfa0768e4c39417'  # wrf0, kub_mean, 2-d

        # Get Observed Data
        model_date_time = datetime.datetime.strptime('%s %s' % (data_date, data_time), '%Y-%m-%d %H:%M:%S')
        print("model_date_time : ", model_date_time)

        kub_time_series = get_kub_mean_timeseries(MySqlAdapter(), model_date_time, kub_observed_id, kub_forecasted_id0,
                                                  kub_forecasted_id1, kub_forecasted_id2, backward)
        kub_rows, kub_columns = kub_time_series.shape
        klb_time_series = get_klb_mean_timeseries(MySqlAdapter(), model_date_time, klb_forecasted_id0, klb_forecasted_id1,
                                                  klb_forecasted_id2, backward)
        klb_rows, klb_columns = klb_time_series.shape
        if (kub_rows > 0) and (klb_rows > 0):
            if kub_rows > klb_rows:
                max_row_count = klb_rows
            else:
                max_row_count = kub_rows

            new_klb_time_series = klb_time_series.head(max_row_count + 1)
            print("klb : ", new_klb_time_series.shape)
            new_kub_time_series = kub_time_series.head(max_row_count + 1)
            print("kub : ", new_kub_time_series.shape)
            time_series_data = new_kub_time_series.merge(new_klb_time_series, left_on='time', right_on='time', how='left',
                                                         suffixes=('_kub', '_klb'))
            time_series_data = time_series_data.sort_values('time')

            ts_start_time = time_series_data.iloc[0]['time']
            ts_end_time = time_series_data.iloc[-1]['time']
            time_duration = (backward + forward) * 24
            ts_actual_end_time = ts_start_time + datetime.timedelta(hours=time_duration-1)

            while ts_end_time < ts_actual_end_time:
                next_ts_time = ts_end_time + datetime.timedelta(hours=1)
                next_ts_time = datetime.datetime.strptime(next_ts_time.strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S')
                time_series_data.loc[len(time_series_data)] = [next_ts_time, float(0), float(0)]
                ts_end_time = time_series_data.iloc[-1]['time']
            try:
                RAIN_CSV_FILE_PATH = os.path.join(RAIN_FALL_DIR, RAIN_CSV_FILE)
                time_series_data.to_csv(RAIN_CSV_FILE_PATH, columns=['time', 'value_kub', 'value_klb'],
                                        encoding='utf-8', header=False, index=False)
            except IOError as ie:
                print("get_rain_fall|IOError|ie: ", ie)
        else:
            print("**********NO DATA**********")
    except IOError as e:
        print("get_rain_fall|IOError|e : ", e)
