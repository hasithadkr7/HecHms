import os


def run_model(run_name, run_date):
    model_path = os.path.join('/home/uwcc-admin/udp_150/hec-hms',run_date.strftime("%Y-%m-%d"), run_name, '2008_2_Events')
    # /home/uwcc-admin/udp_150/hec-hms/2018-07-12/hello/2008_2_Events/2008_2_Events.script
    script_file_path = os.path.join(model_path, '2008_2_Events.script')
    os.system('./run_hec.sh {}'.format(script_file_path))

