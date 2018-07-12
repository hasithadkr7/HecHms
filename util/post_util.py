import os
import subprocess


def dss_to_csv(run_name, run_date):
    date_str = run_date.strftime("%Y-%m-%d")
    model_path = os.path.join(date_str, run_name, '2008_2_Events')
    dssvue_cmd = 'dssvue/hec-dssvue.sh dss_to_csv_util.py --date {} --run_name {} --model_dir {}' \
        .format(date_str, run_name, model_path)
    subprocess.call([dssvue_cmd], shell=True)


