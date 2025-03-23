from flask import Flask, render_template_string, request
from flask_sock import Sock
import threading
import time
import random
import queue
import asyncio
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
devices_table = ['iot_test_dev', 'iot_test_dev2']

# ----------------------------------- FUNCTIONS -----------------------------------
def validate_device(device):
    if device in devices_table:
        return True
    return False

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

@sock.route('/<device>/ws')
def websocket_endpoint(ws, device):
    log.info(f"New websocket connection to /{device}/ws from {request.remote_addr}")

    if validate_device(device) == False:
        log.warning(f"Device not found: {device}")
        ws.send(f"Device not found")
        return
    
    try:
        while True:
            message = ws.receive(timeout=0.2)
            if message:
                log.info(f"New websocket message from {request.remote_addr}")
                log.debug(f"Websocket recieved message: {message}")
                
                if message == "get_db":
                    db = db_measurement(device)
                    data = db.read_all_data()

                    log.info(f"Sending data to client at {request.remote_addr}")
                    ws.send(json.dumps(data))

                else:
                    log.info(f"Sending BAD COMMAND info to client at {request.remote_addr}")
                    ws.send(f"Bad command")

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
