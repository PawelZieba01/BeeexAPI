
import os, certifi, json
from datetime import datetime
from logger import log
from influxdb_client_3 import InfluxDBClient3, flight_client_options, Point

_INFLUXDB_TOKEN='BoQD4N5-fX2FgYUh_e3fqZ1ijZEc9mr3H5GSat1Y1u1avOmrKQ0LRFWAjNXu_nhvwblagZvWM5Xh7ebbBOcSjQ=='
_org = "Dev"
_host = "https://eu-central-1-1.aws.cloud2.influxdata.com"
_database="IOT_Dev"

class database:
    def __init__(self):
        self.cert = None
        self.client = None

        #if OS is Windows use certifi for SSL
        if os.name == 'nt':
            fh = open(certifi.where(), "r")
            cert = fh.read()
            fh.close()

            self.client = InfluxDBClient3(host=_host, token=_INFLUXDB_TOKEN, org=_org, flight_client_options=flight_client_options(tls_root_certs=cert))
        else:
            self.client = InfluxDBClient3(host=_host, token=_INFLUXDB_TOKEN, org=_org)
        
    def write_data(self, data):
        for point in data:
            log.debug(f"Writing data to database: {point}")
        self.client.write(database=_database, record=data)

    def read_data(self, query:str):
        table = self.client.query(query=query, database=_database, language='sql')
        df = table.to_pandas().sort_values(by='time')
        json_data = df.to_json(orient='records', date_format='iso')
        parsed_json_data = json.loads(json_data)
        pretty_json_data = json.dumps(parsed_json_data, indent=4)
        log.debug(f"Data from database: {pretty_json_data}")
        return parsed_json_data
            

class db_measurement(database):
    def __init__(self, name:str):
        self.name = name
        super().__init__()

    def write_data(self, data:dict):
        log.info(f"Writing data to database: {self.name}")
        points = []
        for key in data:
            if self.check_data(data[key]) == False:
                log.warning(f"Data is not valid - ignored data: {data[key]}")
                continue
            log.debug(f"Data is valid - preparing data: {data[key]}")

            point = (
                Point(self.name)
                .tag("type", self.name)
                .field("temperature", data[key]["temperature"])
                .field("humidity", data[key]["humidity"])
                .field("timestamp", int(data[key]["timestamp"]))
                .time(datetime.now())
                )
            points.append(point)
        super().write_data(points)

    def read_all_data(self):
        log.info(f"Reading all data from database: {self.name}")
        query = f"SELECT * FROM {self.name}"
        data = super().read_data(query)
        return data
    
    def check_data(self, data:dict):
        if "temperature" not in data or "humidity" not in data or "timestamp" not in data:
            return False
        return True
    
