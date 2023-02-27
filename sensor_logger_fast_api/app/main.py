from fastapi import FastAPI
from kafka import KafkaProducer
import json
import os

_producer = None
try:
    _producer = KafkaProducer(bootstrap_servers=os.environ.get('KAFKA_BROKER', 'broker1:9093').split(","), 
                              api_version=(0, 10),
                              max_block_ms=10000)
except Exception as ex:
    print('Exception while connecting Kafka')
    print(str(ex))


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


# insert URL into SensorLogger app
# https://github.com/tszheichoi/awesome-sensor-logger/#live-data-streaming
@app.post("/data")
async def data(data: dict):
    print({
            "messageId": data["messageId"],
            "sessionId": data["sessionId"],
            "deviceId": data["deviceId"]
            })
    print(data["payload"])

    try:
        for measurement in data["payload"]:
            timestamp_ms = int(measurement["time"]) // 1_000 # convert nanoseconds to milliseconds
            key_bytes = bytes(f"{measurement['name']}", encoding='utf-8')
            value_bytes = bytes(json.dumps(measurement["values"]), encoding='utf-8')
            _producer.send(os.environ.get('KAFKA_TOPIC', "sensorData"),
                           key=key_bytes,
                           value=value_bytes,
                           timestamp_ms=timestamp_ms) 
        _producer.flush()
        print('Message published successfully.')
    except Exception as ex:
        print('Exception in publishing message')
        print(str(ex))
    
    return {"message": "Sensor data received"}