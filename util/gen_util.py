from db_util import MySqlAdapter, get_init_state, save_init_state
import os


def read_file(filename):
    with open(filename, 'rb') as f:
        file_data = f.read()
    return file_data


def write_file(data, filename):
    with open(filename, 'wb') as f:
        f.write(data)


def is_init_state(date, init_state_path):
    state_data = get_init_state(MySqlAdapter(), date)
    if state_data is not None:
        write_file(state_data, init_state_path)
        return False
    else:
        return True


def save_init_state(date, init_state_path):
    if os.path.exists(init_state_path):
        state_data = read_file(init_state_path)
        save_init_state(MySqlAdapter(), date, state_data)

