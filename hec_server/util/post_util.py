import os
import subprocess


def dss_to_csv(run_name, run_date):
    date = run_date.strftime("%Y-%m-%d")
    time = run_date.strftime("%H:%M:%S")
    model_path = os.path.join('hec-hms', run_date.strftime("%Y-%m-%d"), run_name, 'model')
    dssvue_cmd2 = '/home/uwcc-admin/udp_150/dssvue/hec-dssvue.sh dss_to_csv_util.py --date {} --time {} --hec-hms-model-dir {}' \
        .format(date, time, model_path)
    subprocess.call([dssvue_cmd2], shell=True)


