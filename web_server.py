import datetime
from flask import Flask, request, redirect, url_for, send_from_directory
from flask_json import FlaskJSON, JsonError, json_response
from flask_uploads import UploadSet, configure_uploads
from model_tasks import init_hec_hms_models, run_hec_hms_model, post_model, discharge_file_exists, upload_discharge_data_to_db, init_hec_hms_models_rf_gen
from os import path
import ast


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


@app.route('/hec_hms/', methods=['POST', 'GET'])
def init_default():
    return redirect(url_for('init_hec_hms'))


@app.route('/hec_hms/init-start-single', methods=['POST'])
def init_hec_hms_single():
    req_args = request.args.to_dict()
    # check whether run-name is specified and valid.
    if 'run-name' not in req_args.keys() or not req_args['run-name']:
        raise JsonError(status_=400, description='run-name is not specified.')

    run_name = req_args['run-name']
    run_datetime_str = request.args.get('datetime', default=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), type=str)
    init_state_str = request.args.get('init-state', default=False, type=str)
    init_state = ast.literal_eval(init_state_str)

    # input_dir_rel_path = path.join(run_datetime, run_name, 'input')
    run_datetime = datetime.datetime.strptime(run_datetime_str, '%Y-%m-%d %H:%M:%S')
    input_dir_rel_path = path.join(run_datetime.strftime('%Y-%m-%d'), run_name, 'input')
    # Check whether the given run-name is already taken for today.
    input_dir_abs_path = path.join(UPLOADS_DEFAULT_DEST, input_dir_rel_path)
    # /home/uwcc-admin/udp_150/hec-hms/2018-07-12/<run-name>/input/
    if path.exists(input_dir_abs_path):
        raise JsonError(status_=400, description='run-name: %s is already taken for run date: %s.' % (run_name, run_datetime))

    req_files = request.files
    if 'rainfall' in req_files:
        model_hec.save(req_files['rainfall'], folder=input_dir_rel_path, name='DailyRain.csv')
        init_hec_hms_models(run_name, run_datetime_str, init_state, 'single')
    elif ('forward' in req_args.keys() or req_args['forward']) and ('backward' in req_args.keys() or req_args['backward']):
        backward = request.args.get('datetime', default=2, type=int)
        forward = request.args.get('datetime', default=3, type=int)
        init_hec_hms_models_rf_gen(run_name, run_datetime_str, init_state, backward, forward)
    else:
        raise JsonError(status_=400, description='Missing required input file. Required DailyRain.csv')

    return json_response(status_=200, description='HecHms successfully initialized.')


@app.route('/hec_hms/init-start-distributed', methods=['POST'])
def init_hec_hms_distributed():
    req_args = request.args.to_dict()
    # check whether run-name is specified and valid.
    if 'run-name' not in req_args.keys() or not req_args['run-name']:
        raise JsonError(status_=400, description='run-name is not specified.')
    run_name = req_args['run-name']
    run_datetime = request.args.get('datetime', default=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), type=str)
    init_state = request.args.get('init-state', default=False, type=bool)
    init_hec_hms_models(run_name, run_datetime, init_state, 'distributed')
    return json_response(status_=200, description='Successfully saved files.')


@app.route('/hec_hms/init-run', methods=['POST', 'GET'])
def run_hec_hms():
    req_args = request.args.to_dict()
    if 'run-name' not in req_args.keys() or not req_args['run-name']:
        raise JsonError(status_=400, description='run-name is not specified.')
    run_name = req_args['run-name']
    run_datetime = request.args.get('datetime', default=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), type=str)
    run_hec_hms_model(run_name, run_datetime)
    post_model(run_name, run_datetime)
    return json_response(status_=200, description='HecHms has successfully run.')


@app.route('/hec_hms/upload_data', methods=['POST'])
def upload_hec_data():
    req_args = request.args.to_dict()
    if 'run-name' not in req_args.keys() or not req_args['run-name']:
        raise JsonError(status_=400, description='run-name is not specified.')
    run_name = req_args['run-name']
    run_datetime_str = request.args.get('datetime', default=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        type=str)
    force_insert_str = request.args.get('init-state', default=False, type=str)
    force_insert = ast.literal_eval(force_insert_str)
    if discharge_file_exists(run_name, run_datetime_str):
        raise JsonError(status_=400, description='No output DailyDischarge.csv file')
    upload_discharge_data_to_db(run_name, run_datetime_str, UPLOADS_DEFAULT_DEST, force_insert)

    return json_response(status_=200, description='HecHms data has successfully uploaded.')


if __name__ == '__main__':
    app.run('localhost', 8080)

