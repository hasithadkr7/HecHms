import datetime
from flask import Flask, request, redirect, url_for, send_from_directory
from flask_json import FlaskJSON, JsonError, json_response
from flask_uploads import UploadSet, configure_uploads
from hec_server.model_tasks import init_hec_hms_models


app = Flask(__name__)
FlaskJSON(app)


@app.route('/hec_hms/', methods=['POST', 'GET'])
def init_default():
    return redirect(url_for('init_hec_hms'))


@app.route('/hec_hms/init-start', methods=['POST'])
def init_hec_hms():
    req_args = request.args.to_dict()
    # check whether run-name is specified and valid.
    if 'run-name' not in req_args.keys() or not req_args['run-name']:
        raise JsonError(status_=400, description='run-name is not specified.')
    if 'run-model' not in req_args.keys() or not req_args['run-model']:
        raise JsonError(status_=400, description='run-model is not specified.')
    print("init_hec_hms...")
    run_model = req_args['run-model']   #run-model='single'/'distributed'
    run_name = req_args['run-name']
    run_datetime = request.args.get('datetime', default=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), type=str)
    print(run_datetime)
    print(run_name)
    print(run_model)
    init_hec_hms_models(run_name, run_datetime, run_model)
    return json_response(status_=200, description='Successfully saved files.')


@app.route('/hec_hms/init-run', methods=['POST', 'GET'])
def run_hec_hms():
    req_args = request.args.to_dict()
    return 'Hello World'


@app.route('/hec_hms/init_gen', methods=['POST', 'GET'])
def init_hec_hms_gen():
    print("init_hec_hms_gen...")
    run_datetime = request.args.get('datetime', default=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), type=str)
    backward = request.args.get('datetime', default=2, type=int)
    forward = request.args.get('datetime', default=3, type=int)
    print(backward)
    print(forward)
    print(run_datetime)
    return 'Hello World'


if __name__ == '__main__':
    app.run('localhost', 8080)

