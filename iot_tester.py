import requests
import json
import random
import time
from datetime import datetime, timedelta
from logger import log
import keyboard

device = 'iot_test_dev2' 
server = 'http://127.0.0.1:8000'
endpoint = f'/{device}/save_data'

log.info("Starting the client...")

def prepare_data():
    data = {}
    for i in range(50):
        point = {f"Point{i}": {
                    "timestamp": (datetime.now() + timedelta(seconds=i)).strftime('%Y%m%d%H%M%S'),
                    "temperature": random.randint(1, 100),
                    "humidity": random.randint(1, 100)
                    },
        }
        data.update(point)
        log.debug(f"Prepared Point{i}: {point}")
    return data

def send_data():
    data = prepare_data()
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(f"{server}{endpoint}", data=json.dumps(data), headers=headers)
        if response.status_code == 200:
            log.debug(f'Sent data: {json.dumps(data, indent=4)}\nResponse status code: {response.status_code}')
        else:
            log.warning(f"Server response code: {response.status_code}, payload:\n{response.text}")
    except:
        log.error("Couldn't send data to the server")


keyboard.add_hotkey('ctrl+w', send_data)

while True:
    time.sleep(5)