from fastapi import FastAPI
from kafka import KafkaProducer
import json
import os
import logging

logger = logging.getLogger(__name__)  # the __name__ resolve to "uicheckapp.services"

_producer = None
try:
    _producer = KafkaProducer(bootstrap_servers=os.environ.get('KAFKA_BROKER', 'broker1:9093').split(","), 
                              api_version=(0, 10),
                              max_block_ms=10000)
except Exception as ex:
    logger.error('Exception while connecting Kafka')
    logger.error(str(ex))


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


# insert URL into SensorLogger app: http://100.102.3.111:8080/data?device=Pixel6&person=Florin&activity=running
# https://github.com/tszheichoi/awesome-sensor-logger/#live-data-streaming
@app.post("/data")
async def data(data: dict, activity: str = None, device: str = None, person: str = None):
    try:
        for measurement in data["payload"]:
            timestamp_ms = int(measurement["time"]) // 1_000 # convert nanoseconds to milliseconds
            key_bytes = bytes(f"{person}:{device}:{activity}:{measurement['name']}", encoding='utf-8')
            value_bytes = bytes(json.dumps(measurement["values"]), encoding='utf-8')
            _producer.send(os.environ.get('KAFKA_TOPIC', "sensorData"),
                           key=key_bytes,
                           value=value_bytes,
                           timestamp_ms=timestamp_ms) 
        _producer.flush()
        logger.info('Message published successfully.')
    except Exception as ex:
        logger.error('Exception in publishing message')
        logger.error(str(ex))
    
    return {"message": "Sensor data received"}