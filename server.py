from flask import Flask, render_template_string, request
from flask_sock import Sock
import threading
import time
import json
from logger import log
import keyboard
from queue import Queue
from database import db_measurement
from helpers import *

log.info("Disable werkzeug logs:")
import logging
_log = logging.getLogger('werkzeug')
_log.setLevel(logging.ERROR)
print("")

app = Flask(__name__)
sock = Sock(app)

# devices
devices_table = ['iot_test_dev1', 'iot_test_dev2']

# Processing actions
processing_actions = ['get_data', 'get_mean', 'get_max', 'get_min']

# Global dictionary to store queues for each WebSocket connection
websocket_queues = {}


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
    db = db_measurement(device)
    db.write_data(data)
    return "OK"
    

# ----------------------------------- WEBSOCKET -----------------------------------

@sock.route('/ws')
def websocket_endpoint(ws):
    ws_id = id(ws)

    log.info(f"New websocket connection to /ws from {request.remote_addr}")
    log.info(f"Created queues for WebSocket {id(ws)}")

    websocket_queues[ws_id] = {"in": Queue(), "out": Queue()}
    log.debug(f"Queue: {websocket_queues}")

    try:
        while True:
            message = ws.receive(timeout=0.1)
            # New message
            if message:
                log.info(f"New websocket message from {request.remote_addr}")
                log.debug(f"Websocket recieved message: {message}")

                # Validate data
                is_valid, mess = validate_ws_message(message)
                if is_valid:
                    json_message = json.loads(message)
                    action = json_message["action"]
                    websocket_queues[ws_id]["in"].put(json_message)
                    log.info(f"Message for '{action}' added to processing queue for WebSocket {ws_id}")
                else:
                    log.warning(f"Invalid websocket message: {mess}")
                    ws_send_error(ws, mess)
                    continue
                
            # Queue processing
            if not websocket_queues[ws_id]["out"].empty():
                response = json.dumps( websocket_queues[ws_id]["out"].get() )
                ws_send_message(ws, response)

    except Exception as e:
        log.warning(f'Connection closed: {e}')

        # delete queues for this websocket
        if ws_id in websocket_queues:
            del websocket_queues[ws_id]
            log.info(f"Removed queues for WebSocket {ws_id}")

    

# ----------------------------------- THREADS -----------------------------------

def processing_thread(): 
    log.info("Processing thread started")   
    while True:
        for ws_id, queues in list(websocket_queues.items()):
            if not queues["in"].empty():
                message = queues["in"].get()
                log.info(f"Processing message from WebSocket {ws_id}")
                log.debug(f"Processing message: {message}")
                
                data = message["data"]
                device = data["device"]
                data_range = data["dataRange"]
                action = message["action"]

                # Actions for processing
                log.info(f"Resolve action: {action}")

                db = db_measurement(device)
                db.set_data_range(data_range["start"]["date"], data_range["end"]["date"], data_range["start"]["time"], data_range["end"]["time"])

                if action == "get_data":
                    process_value = db.read_data()
                    log.info(f"Get measurements from database")

                elif action == "get_mean":
                    process_value = prepare_payload_message(("temperature", db.read_mean("temperature")), ("humidity", db.read_mean("humidity")))
                    log.info(f"Get mean value from database")

                elif action == "get_max":
                    process_value = prepare_payload_message(("temperature", db.read_max("temperature")), ("humidity", db.read_max("humidity")))
                    log.info(f"Get max value from database")
                    
                elif action == "get_min":
                    process_value = prepare_payload_message(("temperature", db.read_min("temperature")), ("humidity", db.read_min("humidity")))
                    log.info(f"Get min value from database")
                
                else: 
                    log.warning(f"Unknown process action: {action}")
                    process_value = None
                    
                response = prepare_ws_message(device, action, process_value)
                log.debug(f"Processing result: {response}")
                queues["out"].put(response) 
        time.sleep(0.1)


# ----------------------------------- MAIN -----------------------------------

if __name__ == '__main__':
    worker_thread = threading.Thread(target=processing_thread, daemon=True)
    worker_thread.start()

    app.run(host='0.0.0.0', port=8000)
