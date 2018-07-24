import datetime
from flask import Flask, request, redirect, url_for, send_from_directory
from flask_json import FlaskJSON, JsonError, json_response
from flask_uploads import UploadSet, configure_uploads
from model_tasks import init_single, upload_discharge
from os import path
import ast
from util.pre_util import validate_run_id
from util.run_util import run_hec_model
from util.post_util import convert_dss_to_csv, exists_discharge_file, copy_input_file_to_output, create_output_zip


app = Flask(__name__)
flask_json = FlaskJSON()

UPLOADS_DEFAULT_DEST = '/home/uwcc-admin/udp_150/hec-hms'

# Flask-Uploads configs
app.config['UPLOADS_DEFAULT_DEST'] = path.join(UPLOADS_DEFAULT_DEST, 'hec_hms')
app.config['UPLOADED_FILES_ALLOW'] = 'csv'

# upload set creation
model_hec = UploadSet('modelHec', extensions='csv')

configure_uploads(app, model_hec)
flask_json.init_app(app)


# Gathering required input files to run single hec-hms model
@app.route('/hec_hms/single/init-start', methods=['POST'])
def init_hec_hms_single():
    print('init_hec_hms_single')
    req_args = request.args.to_dict()
    if 'run-name' not in req_args.keys() or not req_args['run-name']:
        raise JsonError(status_=400, description='run-name is not specified.')
    if 'run-datetime' not in req_args.keys() or not req_args['run-datetime']:
        raise JsonError(status_=400, description='run-datetime is not specified.')
    if 'init-state' not in req_args.keys() or not req_args['init-state']:
        raise JsonError(status_=400, description='init-state is not specified.')
    init_state = ast.literal_eval(request.args.get('init-state', type=str))
    run_name = request.args.get('run-name', type=str)
    # Model running date default is current date. Folder created for this date.
    run_datetime = datetime.datetime.strptime(request.args.get('run-datetime', type=str), '%Y-%m-%d %H:%M:%S')
    input_dir_rel_path = path.join(run_datetime.strftime('%Y-%m-%d'), run_name, 'input')
    # Check whether the given run-name is already taken for today.
    input_dir_abs_path = path.join(UPLOADS_DEFAULT_DEST, input_dir_rel_path)
    if path.exists(input_dir_abs_path):
        raise JsonError(status_=400, description='run-name: %s is already taken for run date: %s.' % (run_name, run_datetime))
    req_files = request.files
    if 'rainfall' in req_files:
        model_hec.save(req_files['rainfall'], folder=input_dir_rel_path, name='DailyRain.csv')
        init_single(run_name, run_datetime.strftime('%Y-%m-%d'), init_state)
        run_id = 'HECHMS:single:%s:%s' % (run_datetime.strftime('%Y-%m-%d'), run_name)
        # TODO save run_id in a DB with the status
        return json_response(status_=200, run_id=run_id, description='Successfully saved files.')
    else:
        raise JsonError(status_=400,description='No required input files found, Rainfall file missing in request.')


# Gathering required input files to run distributed hec-hms model
@app.route('/hec_hms/distributed/init-start', methods=['POST'])
def init_hec_hms_distributed():
    print('init_hec_hms_distributed')
    req_args = request.args.to_dict()
    if 'run-name' not in req_args.keys() or not req_args['run-name']:
        raise JsonError(status_=400, description='run-name is not specified.')
    if 'run-datetime' not in req_args.keys() or not req_args['run-datetime']:
        raise JsonError(status_=400, description='run-datetime is not specified.')
    if 'model-datetime' not in req_args.keys() or not req_args['model-datetime']:
        raise JsonError(status_=400, description='model-datetime is not specified.')
    if 'init-state' not in req_args.keys() or not req_args['init-state']:
        raise JsonError(status_=400, description='init-state is not specified.')
    init_state = ast.literal_eval(request.args.get('init-state', type=str))
    run_name = request.args.get('run-name', type=str)
    # Model running date default is current date. Folder created for this date.
    run_datetime = datetime.datetime.strptime(request.args.get('run-datetime', type=str), '%Y-%m-%d %H:%M:%S')
    # Model state date time. Which can be a past date or current date.
    model_datetime = datetime.datetime.strptime(request.args.get('model-datetime', type=str), '%Y-%m-%d %H:%M:%S')
    input_dir_rel_path = path.join(run_datetime.strftime('%Y-%m-%d'), run_name, 'input')
    # Check whether the given run-name is already taken for today.
    input_dir_abs_path = path.join(UPLOADS_DEFAULT_DEST, input_dir_rel_path)
    if path.exists(input_dir_abs_path):
        raise JsonError(status_=400,
                        description='run-name: %s is already taken for run date: %s.' % (run_name, run_datetime))


# Running hec-hms
@app.route('/hec_hms/init-run', methods=['POST'])
def run_hec_hms():
    print('run_hec_hms')
    req_args = request.args.to_dict()
    if 'run-id' not in req_args.keys() or not req_args['run-id']:
        raise JsonError(status_=400, description='run-id is not specified.')
    run_id = request.args.get('run-id', type=str)
    if validate_run_id(run_id):
        run_date = run_id.split(':')[2]
        run_name = run_id.split(':')[3]
        run_hec_model(run_name, run_date)
        convert_dss_to_csv(run_name, run_date)
        return json_response(status_=200, run_id=run_id, description='Successfully run Hec-Hms.')
    else:
        raise JsonError(status_=400, description='Invalid run id.')


# Create zip file with input files, run configurations and output files
@app.route('/hec_hms/upload', methods=['POST'])
def upload_data():
    print('upload_data')
    req_args = request.args.to_dict()
    if 'run-id' not in req_args.keys() or not req_args['run-id']:
        raise JsonError(status_=400, description='run-id is not specified.')
    if 'zip-file-name' not in req_args.keys() or not req_args['zip-file-name']:
        raise JsonError(status_=400, description='zip-file-name is not specified.')
    run_id = request.args.get('run-id', type=str)
    zip_file_name = request.args.get('zip-file-name', type=str)
    if validate_run_id(run_id):
        run_date = run_id.split(':')[2]
        run_name = run_id.split(':')[3]
        input_file_path = path.join(UPLOADS_DEFAULT_DEST, run_date, run_name, 'input')
        output_file_path = path.join(UPLOADS_DEFAULT_DEST, run_date, run_name, 'output')
        copy_input_file_to_output(input_file_path, output_file_path)
        create_output_zip(zip_file_name, output_file_path)
    else:
        raise JsonError(status_=400, description='Invalid run id.')


# Upload discharge data to db by reading DailyDischarge.csv
@app.route('/hec_hms/extract', methods=['POST'])
def extract_data():
    print('extract_data')
    req_args = request.args.to_dict()
    if 'run-id' not in req_args.keys() or not req_args['run-id']:
        raise JsonError(status_=400, description='run-id is not specified.')
    if 'force-insert' not in req_args.keys() or not req_args['force-insert']:
        raise JsonError(status_=400, description='force-insert is not specified.')
    force_insert = ast.literal_eval(request.args.get('force-insert', type=str))
    run_id = request.args.get('run-id', type=str)
    if validate_run_id(run_id):
        run_date = run_id.split(':')[2]
        run_name = run_id.split(':')[3]
        if exists_discharge_file(run_name, run_date, UPLOADS_DEFAULT_DEST):
            upload_discharge(run_name, run_date, UPLOADS_DEFAULT_DEST, force_insert)
            return json_response(status_=200, run_id=run_id, description='Successfully uploaded data.')
        else:
            raise JsonError(status_=400, description='No Discharge data found.')
    else:
        raise JsonError(status_=400, description='Invalid run id.')


