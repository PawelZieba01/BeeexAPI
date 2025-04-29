from time import sleep
from datetime import datetime
from influxdb_client_3 import InfluxDBClient3, Point, flight_client_options
import certifi
import json

# Load the certificate -- Windows only !!!
fh = open(certifi.where(), "r")
cert = fh.read()
fh.close()
# ---------------------------------------#

INFLUXDB_TOKEN=''
org = "Dev"
host = "https://eu-central-1-1.aws.cloud2.influxdata.com"
database="IOT_Dev"

token_file = open("influx_token.txt", "r")
INFLUXDB_TOKEN = token_file.read()
token_file.close()

client = InfluxDBClient3(host=host, token=INFLUXDB_TOKEN, org=org, flight_client_options=flight_client_options(tls_root_certs=cert))

data = {
    "point1": {
        "timestamp": "20250322214700",
        "temperature": 25,
        "humidity": 50,
    },
    "point2": {
        "timestamp": "20250322214700",
        "temperature": 24,
        "humidity": 50,
    },
    "point3": {
        "timestamp": "20250322214700",
        "temperature": 23,
        "humidity": 50,
    },
    "point4": {
        "timestamp": "20250322214700",
        "temperature": 22,
        "humidity": 50,
    },
    "point5": {
        "timestamp": "20250322214700",
        "temperature": 21,
        "humidity": 50,
    },
}

points = []

for key in data:
    point = (
        Point("iot_test_dev")
        .tag("type", "test")
        .field("temperature", data[key]["temperature"])
        .field("humidity", data[key]["humidity"])
        .field("timestamp", data[key]["timestamp"])
        .time(datetime.now())
        )
    points.append(point)
client.write(database=database, record=points)
print("Complete.")


query = "SELECT * FROM iot_data_dev"

# Execute the query
table = client.query(query=query, database=database, language='sql')

print(table)
# Convert to dataframe
df = table.to_pandas().sort_values(by='time')
print(df)
print("")

# Convert dataframe to JSON
json_data = df.to_json(orient='records', date_format='iso')

# Parse JSON data back to Python dictionary
parsed_json_data = json.loads(json_data)

# Pretty-print JSON data with an indentation of 4 spaces
pretty_json_data = json.dumps(parsed_json_data, indent=4)
print("Pretty JSON data:", pretty_json_data)