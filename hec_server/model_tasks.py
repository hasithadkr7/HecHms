import datetime
import json
from distutils.dir_util import copy_tree
import os
from hec_server.util.pre_util import copy_model_files


def init_hec_hms_models(run_name, run_datetime, run_model='single'):
    run_date = datetime.datetime.strptime(run_datetime, '%Y-%m-%d %H:%M:%S')
    if run_model == 'single':
        print('single')
        init_single(run_name, run_date)
    elif run_model == 'distributed':
        print('distributed')


def init_single(run_name, run_date):
    print('init_single')
    copy_model_files(run_name, run_date)


def init_distributed(run_name, run_date):
    print('')

