import pymysql
import pymysql.cursors
import pandas as pd


class MySqlAdapter:
    def __init__(self, host="localhost", user="root", password="", db="curw"):
        self.connection = pymysql.connect(host=host,
                                          user=user,
                                          password=password,
                                          db=db)


def get_time_series_values(self, event_id, data_from, data_to):
    sql = "SELECT `time`,`value` FROM `%s` WHERE `id`=\"%s\" " % ('data', event_id)
    sql += "AND `%s`>=\"%s\" " % ('time', data_from)
    sql += "AND `%s`<=\"%s\" " % ('time', data_to)
    #print('------------------------------sql: ', sql)
    with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(sql)
        time_series_data = pd.DataFrame(cursor.fetchall())
        return time_series_data
    print("LOG---No data found.")
    return pd.DataFrame(columns=['time', 'value'])


