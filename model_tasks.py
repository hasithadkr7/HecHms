import datetime
from util.pre_util import copy_model_files, generate_rainfall, update_model_files, update_model, csv_to_dss
from util.post_util import dss_to_csv
from util.run_util import run_model


def init_hec_hms_models(run_name, run_datetime, init_state, run_model='single'):
    run_date = datetime.datetime.strptime(run_datetime, '%Y-%m-%d %H:%M:%S')
    if run_model == 'single':
        print('single')
        init_single(run_name, run_date, init_state)
    elif run_model == 'distributed':
        print('distributed')


def init_single(run_name, run_date, init_state):
    print('init_single')
    copy_model_files(run_name, run_date)
    generate_rainfall(run_name, run_date)
    update_model_files(run_name, run_date, init_state)
    update_model(run_name, run_date)
    csv_to_dss(run_name, run_date)


def init_distributed(run_name, run_date):
    print('')


def run_hec_hms_model(run_name, run_datetime):
    run_date = datetime.datetime.strptime(run_datetime, '%Y-%m-%d %H:%M:%S')
    run_model(run_name, run_date)


def post_model(run_name, run_datetime):
    run_date = datetime.datetime.strptime(run_datetime, '%Y-%m-%d %H:%M:%S')
    dss_to_csv(run_name, run_date)

