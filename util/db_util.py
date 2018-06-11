import pandas as pd
import hashlib
import json
import traceback
from pandas.io import sql
import MySQLdb
from sqlalchemy import create_engine
import datetime


class MySqlAdapter:
    def __init__(self):
        CONFIG = json.loads(open('/home/uwcc-admin/udp_150/HecHms/config.json').read())
        if 'MYSQL_HOST' in CONFIG:
            MYSQL_HOST = CONFIG['MYSQL_HOST']
        if 'MYSQL_USER' in CONFIG:
            MYSQL_USER = CONFIG['MYSQL_USER']
        if 'MYSQL_DB' in CONFIG:
            MYSQL_DB = CONFIG['MYSQL_DB']
        if 'MYSQL_PASSWORD' in CONFIG:
            MYSQL_PASSWORD = CONFIG['MYSQL_PASSWORD']
        connection_string = 'mysql://{}:{}@{}/{}'.format(MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DB)
        self.engine = create_engine(connection_string)
        self.meta_struct = {
            'station': '',
            'variable': '',
            'unit': '',
            'type': '',
            'source': '',
            'name': ''
        }
        self.meta_struct_keys = sorted(self.meta_struct.keys())

        self.station_struct = {
            'id': '',
            'stationId': '',
            'name': '',
            'latitude': '',
            'longitude': '',
            'resolution': '',
            'description': ''
        }
        self.station_struct_keys = self.station_struct.keys()

        self.source_struct = {
            'id': '',
            'source': '',
            'parameters': ''
        }
        self.source_struct_keys = self.source_struct.keys()


def get_time_series_values(self, event_id, data_from, data_to):
    sql = "SELECT `time`,`value` FROM `%s` WHERE `id`=\"%s\" " % ('data', event_id)
    sql += "AND `%s`>=\"%s\" " % ('time', data_from)
    sql += "AND `%s`<=\"%s\" " % ('time', data_to)
    time_series_data = pd.read_sql_query(sql, self.engine)
    return time_series_data


def save_time_series_values(self, data_frame):
    try:
        data_frame.to_sql(name='data', con=self.engine, if_exists='append', index=False)
    except Exception:
        traceback.print_exc()

def get_event_id(self, meta_data):
    event_id = None
    m = hashlib.sha256()
    hash_data = dict(self.meta_struct)
    for i, value in enumerate(self.meta_struct_keys):
        hash_data[value] = meta_data[value]

    m.update(json.dumps(hash_data, sort_keys=True).encode("ascii"))
    possible_id = m.hexdigest()
    try:
        connection = self.engine.connect()
        result = connection.execute("SELECT 1 FROM `run` WHERE `id`='{}'".format(possible_id))
        if result.fetchone() is not None:
            event_id = possible_id
    except Exception:
        traceback.print_exc()
    finally:
        return event_id


def create_event_id(self, meta_data):
    hash_data = dict(self.meta_struct)
    for i, value in enumerate(self.meta_struct_keys):
        hash_data[value] = meta_data[value]
    m = hashlib.sha256()
    m.update(json.dumps(hash_data, sort_keys=True).encode("ascii"))
    event_id = m.hexdigest()
    try:
        sql_list = [
            "SELECT `id` as `station_id` FROM `station` WHERE `name`='{}'".format(meta_data['station']),
            "SELECT `id` as `variable_id` FROM `variable` WHERE `variable`='{}'".format(meta_data['variable']),
            "SELECT `id` as `unit_id` FROM `unit` WHERE `unit`='{}'".format(meta_data['unit']),
            "SELECT `id` as `type_id` FROM `type` WHERE `type`='{}'".format(meta_data['type']),
            "SELECT `id` as `source_id` FROM `source` WHERE `source`='{}'".format(meta_data['source'])
        ]
        station_id = self.engine.connect().excute(sql_list[0]).fetchone()
        variable_id = self.engine.connect().excute(sql_list[1]).fetchone()
        unit_id = self.engine.connect().excute(sql_list[2]).fetchone()
        type_id = self.engine.connect().excute(sql_list[3]).fetchone()
        source_id = self.engine.connect().excute(sql_list[4]).fetchone()

        sql = "INSERT INTO `run` (`id`, `name`, `station`, `variable`, `unit`, `type`, `source`) VALUES ({},{},{},{},{},{},{})"\
            .format((event_id,meta_data['name'],station_id,variable_id,unit_id,type_id,source_id))
        self.engine.connect().excute(sql)
    except Exception as e:
        traceback.print_exc()
        raise e
    finally:
        return event_id


def get_type_from_date_time(date_time, type):
    if isinstance(date_time, str):
        date_time = datetime.datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')
    if type == 'Forecast-0-d':
        return 2
    elif type == 'Forecast-1-d-after':
        return 3
    elif type == 'Forecast-2-d-after':
        return 3
    elif type == 'Forecast-3-d-after':
        return 3
    elif type == 'Forecast-4-d-after':
        return 3
    elif type == 'Forecast-5-d-after':
        return 3
    elif type == 'Forecast-6-d-after':
        return 3
    elif type == 'Forecast-7-d-after':
        return 3
    elif type == 'Forecast-8-d-after':
        return 3
    elif type == 'Forecast-9-d-after':
        return 3


def get_type_by_date(run_date, ts_date):
    if isinstance(run_date, str):
        run_date = datetime.datetime.strptime(run_date, '%Y-%m-%d')
    if isinstance(ts_date, str):
        ts_date = datetime.datetime.strptime(ts_date, '%Y-%m-%d')
    if ts_date == run_date:
        return 'Forecast-0-d'
    elif ts_date == run_date + datetime.timedelta(days=1):
        return 'Forecast-1-d-after'
    elif ts_date == run_date + datetime.timedelta(days=2):
        return 'Forecast-2-d-after'
    elif ts_date == run_date + datetime.timedelta(days=3):
        return 'Forecast-3-d-after'
    elif ts_date == run_date + datetime.timedelta(days=4):
        return 'Forecast-4-d-after'
    elif ts_date == run_date + datetime.timedelta(days=5):
        return 'Forecast-5-d-after'
    elif ts_date == run_date + datetime.timedelta(days=6):
        return 'Forecast-6-d-after'
    elif ts_date == run_date + datetime.timedelta(days=7):
        return 'Forecast-7-d-after'
    elif ts_date == run_date + datetime.timedelta(days=8):
        return 'Forecast-8-d-after'
    elif ts_date == run_date + datetime.timedelta(days=9):
        return 'Forecast-9-d-after'
    else:
        return 'Error'

