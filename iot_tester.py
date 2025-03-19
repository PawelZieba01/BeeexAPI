import requests
import json
import random
import time
from datetime import datetime
from logger import logger

server = 'http://127.0.0.1:8000'
endpoint = '/test_device/save_data'

log = logger(["DEBUG", "INFO", "WARNING", "ERROR"])
log.info("Starting the client...")

while True:
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data = {'value': random.randint(1, 100), 'timestamp': timestamp}
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(f"{server}{endpoint}", data=json.dumps(data), headers=headers)
        if response.status_code == 200:
            log.debug(f'Sent data: {data}, Response status code: {response.status_code}')
        else:
            log.warning(f"Server response code: {response.status_code}, payload:\n{response.text}")
    except:
        log.error("Couldn't send data to the server")

    time.sleep(5)