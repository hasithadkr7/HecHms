import os
import subprocess
from distutils.dir_util import copy_tree
from shutil import make_archive


def dss_to_csv(run_name, run_date):
    date_str = run_date.strftime("%Y-%m-%d")
    model_path = os.path.join(date_str, run_name, '2008_2_Events')
    dssvue_cmd = 'dssvue/hec-dssvue.sh dss_to_csv_util.py --date {} --run_name {} --model_dir {}' \
        .format(date_str, run_name, model_path)
    subprocess.call([dssvue_cmd], shell=True)


def convert_dss_to_csv(run_name, run_date):
    model_path = os.path.join(run_date, run_name, '2008_2_Events')
    dssvue_cmd = 'dssvue/hec-dssvue.sh dss_to_csv_util.py --date {} --run_name {} --model_dir {}' \
        .format(run_date, run_name, model_path)
    subprocess.call([dssvue_cmd], shell=True)


def discharge_file_exists(run_name, run_date, output_path_prefix):
    date_str = run_date.strftime("%Y-%m-%d")
    discharge_file = os.path.join(output_path_prefix, date_str, run_name, 'output/DailyDischarge.csv')
    os.path.isfile(discharge_file)


def exists_discharge_file(run_name, run_date, output_path_prefix):
    discharge_file = os.path.join(output_path_prefix, run_date, run_name, 'output/DailyDischarge.csv')
    os.path.isfile(discharge_file)


def copy_input_file_to_output(source,destination):
    copy_tree(source, destination)


def zipdir(path, ziph):
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))


def create_output_zip(zip_file_name, input_file_path, output_file_path):
    output_zip = zip_file_name + '.zip'
    output_zip_abs_path = os.path.join(output_file_path, output_zip)

    # Check whether output.zip is already created.
    if os.path.exists(output_zip_abs_path):
        return output_zip

    # Check whether the output is ready. If ready archive and return the .zip, otherwise return None.
    if os.path.exists(output_file_path):
        make_archive(input_file_path, 'zip', output_file_path)
        return output_zip



