import os


def run_model(run_name, run_date):
    model_path = os.path.join('hec-hms', run_date.strftime("%Y-%m-%d"), run_name, 'model')
    script_file_path = os.path.join(model_path, run_name + '.script')
    os.system('./run_hec.sh {}'.format(script_file_path))

