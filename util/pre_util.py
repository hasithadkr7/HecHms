import os
import subprocess
from distutils.dir_util import copy_tree
from get_rain_fall import generate_rf_file
from model_update_util import update_model_configs, update_model_script


def copy_model_files(run_name, folder_date):
    print("copy_model_files")
    model_path = os.path.join(folder_date, run_name, '2008_2_Events')
    base_model_path = os.path.join('2008_2_Events_Hack')
    if not os.path.exists(model_path):
        os.makedirs(model_path)
    print(model_path)
    copy_tree(base_model_path, model_path)


def generate_rainfall(run_name, run_date, backward=2, forward=3):
    input_path = os.path.join(run_date.strftime("%Y-%m-%d"), run_name, 'input')
    if not os.path.exists(input_path):
        os.makedirs(input_path)
    date = run_date.strftime("%Y-%m-%d")
    time = run_date.strftime("%H:%M:%S")
    generate_rf_file(input_path, date, time, backward, forward)


def update_model_files(run_name, folder_date, init_state):
    control_file = os.path.join(folder_date, run_name, '2008_2_Events/Control_1.control')
    run_file = os.path.join(folder_date, run_name, '2008_2_Events/2008_2_Events.run')
    gage_file = os.path.join(folder_date, run_name, '2008_2_Events/2008_2_Events.gage')
    rainfall_file = os.path.join(folder_date, run_name, 'input/DailyRain.csv')
    update_model_configs(control_file, run_file, gage_file, rainfall_file, init_state)


def update_model(run_name, folder_date):
    model_path = os.path.join(folder_date, run_name, '2008_2_Events')
    if not os.path.exists(model_path):
        os.makedirs(model_path)
    update_model_script(model_path, '2008_2_Events')


def csv_to_dss(run_name, folder_date):
    model_path = os.path.join(folder_date, run_name, '2008_2_Events')
    dssvue_cmd = 'dssvue/hec-dssvue.sh csv_to_dss_util.py --date {} --run_name {} --model_dir {}' \
        .format(folder_date, run_name, model_path)
    subprocess.call([dssvue_cmd], shell=True)


def validate_run_id(run_id):
    print(run_id)
    run_id_part_list = run_id.split(':')
    if len(run_id_part_list) == 4:
        return True
    else:
        return False


