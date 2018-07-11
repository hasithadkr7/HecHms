import os
import subprocess
from distutils.dir_util import copy_tree
from hec_server.get_rain_fall import generate_rf_file
from hec_server.model_update_util import update_model_configs, update_model_script


def copy_model_files(run_name, run_date):
    print("copy_model_files")
    model_path = os.path.join('/home/hec-hms', run_date.strftime("%Y-%m-%d"), run_name, 'model')
    base_model_path = os.path.join('/home/hec-hms', '2008_2_Events_Hack')
    if not os.path.exists(model_path):
        os.makedirs(model_path)
    print(model_path)
    copy_tree(base_model_path, model_path)


def generate_rainfall(run_name, run_date, backward=2, forward=3):
    input_path = os.path.join('/home/hec-hms', run_date.strftime("%Y-%m-%d"), run_name, 'input')
    if not os.path.exists(input_path):
        os.makedirs(input_path)
    date = run_date.strftime("%Y-%m-%d")
    time = run_date.strftime("%H:%M:%S")
    generate_rf_file(input_path, date, time, backward, forward)


def update_model_files(run_name, run_date):
    date = run_date.strftime("%Y-%m-%d")
    time = run_date.strftime("%H:%M:%S")
    control_file = os.path.join('/home/hec-hms', run_date.strftime("%Y-%m-%d"), run_name, 'input/Control_1.control')
    run_file = os.path.join('/home/hec-hms', run_date.strftime("%Y-%m-%d"), run_name, 'input/2008_2_Events.run')
    gage_file = os.path.join('/home/hec-hms', run_date.strftime("%Y-%m-%d"), run_name, 'input/2008_2_Events.gage')
    update_model_configs(control_file, run_file, gage_file, date, time)


def update_model(run_name, run_date):
    model_path = os.path.join('hec-hms', run_date.strftime("%Y-%m-%d"), run_name, 'model')
    if not os.path.exists(model_path):
        os.makedirs(model_path)
    update_model_script(model_path, run_name)


def csv_to_dss(run_name, run_date):
    date_str = run_date.strftime("%Y-%m-%d")
    time_str = run_date.strftime("%H:%M:%S")
    model_path = os.path.join('/home/hec-hms', date_str, run_name, 'model')
    dssvue_cmd = 'dssvue/hec-dssvue.sh csv_to_dss_util.py --date {} --time {} --hec-hms-model-dir {}' \
        .format(date_str, time_str, model_path)
    subprocess.call([dssvue_cmd], shell=True)


