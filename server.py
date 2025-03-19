from flask import Flask, render_template_string, request
from flask_sock import Sock
import threading
import time
import random
import queue
import asyncio
from logger import logger

# Disable werkzeug logs
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

log = logger(["DEBUG", "INFO", "WARNING", "ERROR"])

app = Flask(__name__)
sock = Sock(app)

glob_num = 0

# simple database
simple_db = []

@app.route('/')
def index():
    log.info("New HTTP GET connection to /")
    with open("index.html", "r") as html:
        return render_template_string(html.read())
    
@app.route('/<device>/save_data', methods=['POST'])
def save_data(device):
    log.info(f"New HTTP POST connection to /{device}/save_data")

    if(device == 'test_device'):
        data = request.get_json()
        log.debug(f"Recieved data: {data}")
        simple_db.append(data)
        return "OK"
    else:
        log.warning(f"Device not found: {device})")
        return "Device not found", 404 
    
@sock.route('/ws')
def websocket_endpoint(ws):
    try:
        while True:
            message = ws.receive(timeout=0.2)
    except Exception as e:
        log.info(f'Connection closed: {e}')

# ----------------------------------- THREADS -----------------------------------

def processing_thread():
    while True:
        time.sleep(1)

# ----------------------------------- MAIN -----------------------------------

if __name__ == '__main__':
    worker_thread = threading.Thread(target=processing_thread, daemon=True)
    worker_thread.start()

    app.run(host='0.0.0.0', port=8000)
