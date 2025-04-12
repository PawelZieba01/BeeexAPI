from server import devices_table, processing_actions
from server import log
import json

# ----------------------------------- HELPER FUNCTIONS -----------------------------------

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
    
    if "dataRange" not in data:
        return False, "Missing 'dataRange' key in data"
    
    dataRange = data["dataRange"]
    if "start" not in dataRange:
        return False, "Missing 'start' key in dataRange"
    
    if "end" not in dataRange:
        return False, "Missing 'end' key in dataRange"
    
    device = data["device"]
    if validate_device(device) == False:
        return False, "Device not found"
    
    action = json_message["action"]
    if action not in processing_actions:
        return False, "Unknown action"
    
    return True, ""
  


def is_json(myjson):
  try:
    json.loads(myjson)
  except ValueError as e:
    return False
  return True



def prepare_ws_message(device, action, payload):
    message = {
        "action": action,
        "data": {
            "device": device,
            "payload": payload
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



def prepare_payload_message(*args):
    payload = {}
    for arg in args:
        key, value = arg
        payload[key] = value
    log.debug(f"Payload: {payload}")
    return payload



def ws_send_message(ws, message):
    log.info(f"Send response to client")
    log.debug(f"Response:\n{message}")
    ws.send(message)



def ws_send_error(ws, error):
    response = prepare_error_message(error)
    ws_send_message(ws, response)
