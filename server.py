from flask import Flask, render_template_string, request
from flask_sock import Sock
import threading
import time
import json
from logger import log
import keyboard
from database import db_measurement

log.info("Disable werkzeug logs:")
import logging
_log = logging.getLogger('werkzeug')
_log.setLevel(logging.ERROR)
print("")

app = Flask(__name__)
sock = Sock(app)

glob_num = 0

# simple database
simple_db = {}

# devices
devices_table = ['iot_test_dev1', 'iot_test_dev2']

# ----------------------------------- FUNCTIONS -----------------------------------
def validate_device(device):
    if device in devices_table:
        return True
    return False

def is_json(myjson):
  try:
    json.loads(myjson)
  except ValueError as e:
    return False
  return True

def preprare_measurements_message(device, measurements):
    message = {
        "action": "measurements",
        "data": {
            "device": device,
            "measurements": measurements
        }
    }
    return message

def prepare_error_message(error):
    message = {
        "action": "error",
        "data": {
            "message": error
        }
    }
    return message

def ws_send_message(ws, message):
    log.debug(f"Response:\n{json.dumps(message, indent=4)}")
    ws.send(json.dumps(message))
    log.info(f"Send response to client")

def ws_send_error(ws, error):
    response = prepare_error_message(error)
    ws_send_message(ws, response)

# ----------------------------------- ROUTES -----------------------------------

@app.route('/')
def index():
    log.info(f"New HTTP GET connection to / from {request.remote_addr}")
    with open("index.html", "r") as html:
        return render_template_string(html.read())
    
@app.route('/<device>/save_data', methods=['POST'])
def save_data(device):
    log.info(f"New HTTP POST connection to /{device}/save_data from {request.remote_addr}")

    if validate_device(device) == False:
        log.warning(f"Device not found: {device}")
        return "Device not found", 404

    data = request.get_json()
    log.debug(f"Recieved data: {json.dumps(data, indent=4)}")
    db = db_measurement(device)
    db.write_data(data)
    return "OK"
    
# ----------------------------------- WEBSOCKET -----------------------------------

@sock.route('/ws')
def websocket_endpoint(ws):
    log.info(f"New websocket connection to /ws from {request.remote_addr}")

    try:
        while True:
            message = ws.receive(timeout=0.2)
            if message:
                log.info(f"New websocket message from {request.remote_addr}")
                log.debug(f"Websocket recieved message: {message}")

                if not is_json(message):
                    log.warning(f"Invalid json format: {message}")
                    ws_send_error(ws, "Invalid json format")
                    continue

                json_message = json.loads(message)
                if "action" not in json_message:
                    log.warning(f"Missing 'action' key in json message: {message}")
                    ws_send_error(ws, "Missing 'action' key in json message")
                    continue

                if "data" not in json_message:
                    log.warning(f"Missing 'action' key in json message: {message}")
                    ws_send_error(ws, "Missing 'data' key in json message")
                    continue

                action = json_message["action"]
                data = json_message["data"]

                if action == "get_data":
                    log.info(f"Action: {action}")

                    if "device" not in data:
                        log.warning(f"Missing 'device' key in data: {data}")
                        ws_send_error(ws, "Missing 'device' key in data")
                        continue

                    device = data["device"]
                    if validate_device(device) == False:
                        log.warning(f"Device not found: {device}")
                        ws_send_error(ws, "Device not found")
                        continue

                    db = db_measurement(device)

                    measurements = db.read_all_data()                    
                    log.info(f"Get measurements from database")
                    
                    response = preprare_measurements_message(device, measurements)
                    ws_send_message(ws, response)
                elif action == "":
                    pass
                else:
                    log.warning(f"Unknown action: {action}")
                    ws_send_error(ws, "Unknown action")

    except Exception as e:
        log.info(f'Connection closed: {e}')

# ----------------------------------- THREADS -----------------------------------

def processing_thread():
    while True:
        time.sleep(1)

# ----------------------------------- MAIN -----------------------------------

keyboard.add_hotkey('ctrl+q', lambda: log.debug(f"Simple database: {json.dumps(simple_db, indent=4)}"))

if __name__ == '__main__':
    worker_thread = threading.Thread(target=processing_thread, daemon=True)
    worker_thread.start()

    app.run(host='0.0.0.0', port=8000)
