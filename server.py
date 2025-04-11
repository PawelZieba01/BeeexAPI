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

def validate_ws_message(message):
    if not is_json(message):
        log.warning(f"Invalid json format: {message}")
        return (False, "Invalid json format")

    json_message = json.loads(message)
    log.debug(f"Message in json format: {json.dumps(json_message, indent=4)}")
    if "action" not in json_message:
        return False, "Missing 'action' key in json message"

    if "data" not in json_message:
        return False, "Missing 'data' key in json message"
    
    data = json_message["data"]
    if "device" not in data:
        return False, "Missing 'device' key in data"
    
    device = data["device"]
    if validate_device(device) == False:
        return False, "Device not found"
    
    if "dataRange" not in data:
        return False, "Missing 'dataRange' key in data"
    
    dataRange = data["dataRange"]
    if "start" not in dataRange:
        return False, "Missing 'start' key in dataRange"
    
    if "end" not in dataRange:
        return False, "Missing 'end' key in dataRange"
    
    return True, ""
  
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
    return json.dumps(message)

def ws_send_message(ws, message):
    log.info(f"Send response to client")
    log.debug(f"Response:\n{message}")
    ws.send(message)

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
        return prepare_error_message("Device not found"), 404
    
    if is_json(request.data) == False:
        log.warning(f"Data is not in json format")
        return prepare_error_message("Data is not in json format"), 404

    data = request.get_json()
    log.debug(f"Recieved data: {json.dumps(data, indent=4)}")
    log.debug(f"Received characters: {json.dumps(data)}")  # Print received characters
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

                # Validate data
                err, mess = validate_ws_message(message)
                if err == False:
                    log.warning(f"Invalid websocket message: {mess}")
                    ws_send_error(ws, mess)
                    continue
                
                # Valid Data
                json_message = json.loads(message)
                action = json_message["action"]
                data = json_message["data"]
                device = data["device"]
                data_range = data["dataRange"]

                # Actions 
                if action == "get_data":
                    log.info(f"Action: {action}")

                    db = db_measurement(device)
                    measurements = db.read_data_range(data_range["start"]["date"], data_range["end"]["date"], data_range["start"]["time"], data_range["end"]["time"])                    
                    log.info(f"Get measurements from database")

                    if len(measurements) == 0:
                        log.warning(f"Database response measurements is empty")
                        ws_send_error(ws, "Measurements is empty")
                        continue
                    
                    response = json.dumps( preprare_measurements_message(device, measurements) )
                    ws_send_message(ws, response)

                elif action == "":
                    pass

                else:
                    log.warning(f"Unknown action: {action}")
                    ws_send_error(ws, "Unknown action")

    except Exception as e:
        log.warning(f'Connection closed: {e}')

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
