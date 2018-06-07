import json
import shutil
import os
import subprocess
import getopt
import sys
from util.model_update_util import update_model_configs, update_model_script


def usage():
    usage_text = """
Usage: ./CSVTODAT.py [-d YYYY-MM-DD] [-t HH:MM:SS] [-h]

-h  --help          Show usage
-d  --date          Date in YYYY-MM-DD. Default is current date. Forecast run date.
-t  --time          Time in HH:MM:SS. Default is current time.
-b  --backward      Back number of days.
"""
    print(usage_text)


try:
    CONFIG = json.loads(open('/home/hasitha/PycharmProjects/HecHms/config.json').read())
    RAIN_FALL_DIR = ''
    HEC_HMS_MODEL_DIR = ''
    HEC_HMS_MODEL_HACK_DIR = ''
    DSS_INPUT_FILE = ''
    DSS_OUTPUT_FILE = ''
    run_date = ''
    run_time = ''
    backward = 2
    forecast_date = ''
    forecast_time = ''

    if 'RAIN_FALL_DIR' in CONFIG:
        RAIN_FALL_DIR = CONFIG['RAIN_FALL_DIR']
    if 'DAYS_SHIFT' in CONFIG:
        DAYS_SHIFT = int(CONFIG['DAYS_SHIFT'])
    if 'HEC_HMS_MODEL_DIR' in CONFIG:
        HEC_HMS_MODEL_DIR = CONFIG['HEC_HMS_MODEL_DIR']
    if 'HEC_HMS_MODEL_NAME' in CONFIG:
        HEC_HMS_MODEL_NAME = CONFIG['HEC_HMS_MODEL_NAME']
    if 'HEC_HMS_MODEL_HACK_DIR' in CONFIG:
        HEC_HMS_MODEL_HACK_DIR = CONFIG['HEC_HMS_MODEL_HACK_DIR']
    if 'DSS_INPUT_FILE' in CONFIG:
        DSS_INPUT_FILE = CONFIG['DSS_INPUT_FILE']
    if 'DSS_OUTPUT_FILE' in CONFIG:
        DSS_OUTPUT_FILE = CONFIG['DSS_OUTPUT_FILE']

    if 'MYSQL_HOST' in CONFIG:
        MYSQL_HOST = CONFIG['MYSQL_HOST']
    if 'MYSQL_USER' in CONFIG:
        MYSQL_USER = CONFIG['MYSQL_USER']
    if 'MYSQL_DB' in CONFIG:
        MYSQL_DB = CONFIG['MYSQL_DB']
    if 'MYSQL_PASSWORD' in CONFIG:
        MYSQL_PASSWORD = CONFIG['MYSQL_PASSWORD']

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:t:p:f:b:", [
            "help", "date=", "time=", "path=", "forward=", "backward="
        ])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-d", "--date"):  # model run date
            date = arg
        elif opt in ("-t", "--time"):  # model run time
            time = arg
        elif opt in ("-b", "--backward"):
            backward = int(arg)
    try:
        shutil.copytree(HEC_HMS_MODEL_HACK_DIR, HEC_HMS_MODEL_DIR)
        os.remove(DSS_INPUT_FILE)
        os.remove(DSS_OUTPUT_FILE)
        try:
            dssvue_cmd = './dssvue/hec-dssvue.sh csv_to_dss_util.py --date {} --time {} --hec-hms-model-dir{}'\
                .format(date, time, HEC_HMS_MODEL_DIR)
            subprocess.call([dssvue_cmd])
            try:
                update_model_configs()
                try:
                    update_model_script(HEC_HMS_MODEL_DIR, HEC_HMS_MODEL_NAME)
                    try:
                        model_script = HEC_HMS_MODEL_NAME + '.script'
                        script_file_path = os.path.join(HEC_HMS_MODEL_DIR, HEC_HMS_MODEL_NAME + '.script')
                        hec_hms_cmd = './hec_hms/HEC-HMS.sh -s {}'.format(script_file_path)
                        subprocess.call([hec_hms_cmd])
                        try:
                            print('')
                        except Exception as something:
                            print('')
                    except Exception as hec_hms_ex:
                        print("Running hec-hms.sh exception|Exception|hec_hms_ex: ",hec_hms_ex)
                except Exception as update_model_script_ex:
                    print("update_model_script|Exception|update_model_script_ex: ", update_model_script_ex)
            except Exception as model_update_ex:
                print("update_model_configs|Exception|model_update_ex: ", model_update_ex)
        except Exception as ex:
            print("Running hec-dssvue.sh exception|Exception|ex: ", ex)
    except OSError as osr:
        print("Model folder copying exception|OSError|osr: ", osr)
except IOError as io:
    print("Config file read exception|IOError|io: ", io)

