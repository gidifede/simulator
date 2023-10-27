import time
import json
from flask import Flask, request
from flask import send_from_directory
# import engine
from models.route import Route
from models.facility import Facility
from models.parcel import Parcel
from models.vehicle import Vehicle
from flask_cors import CORS
from models.ref import get_instances
from logistic_environment import LogisticsEnvironment
import os

app = Flask(__name__)
CORS(app)

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if not isinstance(obj, (Route, Facility, Parcel, Vehicle)):
            return super(MyEncoder, self).default(obj)

        return obj.json()

@app.route("/facilities")
def summary():

    return json.loads(json.dumps(list(logistics_env.facility_manager.facilities), cls=MyEncoder))

@app.route("/vehicles")
def vehicles():
    return json.loads(json.dumps(list(logistics_env.fleet_manager.vehicles), cls=MyEncoder))

@app.route("/")
def index():
    return send_from_directory('.', "index.html")

@app.route("/time")
def time():
    return logistics_env.get_time()

@app.route("/toggle_paused")
def toggle_paused():
    return str(logistics_env.toggle_paused())

@app.route("/paused")
def paused():
    return str(logistics_env.get_paused())

@app.route("/set_auto_mode")
def set_auto_mode():
    return logistics_env.set_auto_mode()

@app.route("/set_manual_mode")
def set_manual_mode():
    return logistics_env.set_manual_mode()

@app.route("/go_ahead_one_step")
def go_ahead_one_step():
    return logistics_env.go_ahead_one_step()

@app.route("/get_cmds_performance")
def get_cmds_performance():
    return logistics_env.get_cmds_performance()

@app.route("/reset")
def reset():
    global logistics_env
    res = logistics_env.reset_flag.set()
    while logistics_env.is_alive():
        print("Restarting...")
    print("init engine...")
    send_commands_flag = True
    # send_commands_flag = False
    logistics_env = LogisticsEnvironment(velocity=3600, send_commands_flag=send_commands_flag)#86400)
    logistics_env.start()
    print(os.environ)
    return str(res)

@app.route("/velocity", methods=["GET", "POST"])
def velocity():
    if request.method == 'POST':
        velocity = int(request.get_data())
        return str(logistics_env.update_velocity(velocity))
    else:
        return str(logistics_env.get_velocity())

@app.route("/parcels/accept", methods=["POST"])
def add_parcel_to_facility():
    parcels = request.get_json()
    print(parcels)
    results = []
    for parcel_dict in parcels:
        parcel = Parcel(**parcel_dict)
        cmd, res = logistics_env.facility_manager.accept_parcel(parcel=parcel, start_datetime=logistics_env.start_datetime, accept_time=0)
        results.append(res)
    return json.dumps(results, cls=MyEncoder)

@app.route("/monitor_url")
def monitor_url():
    return os.environ.get("MONITOR_URL", "http://localhost:5555")

print("init engine...")

send_commands_flag = True
# send_commands_flag = False
logistics_env = LogisticsEnvironment(velocity=3600, send_commands_flag=send_commands_flag)#86400)
logistics_env.start()

print(os.environ)