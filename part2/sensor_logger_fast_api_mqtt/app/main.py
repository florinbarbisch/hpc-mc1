from fastapi import FastAPI
import paho.mqtt.client as mqtt
import uuid
import json
import os
import logging

logger = logging.getLogger(__name__)  # the __name__ resolve to "uicheckapp.services"


client = mqtt.Client(client_id="cpu-logger-" + str(uuid.uuid4()))
client.loop_start()


try:
    client.connect(os.environ.get('MQTT_BROKER', "mosquitto1"))
except Exception as ex:
    logger.error('Exception while connecting to MQTT Broker', exc_info=True)


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
            timestamp_ms = int(measurement["time"]) // 1_000_000 # convert nanoseconds to milliseconds
            topic = f"sensors/{person}/{device}/{activity}/{measurement['name']}"
            # add timestamp to measurement["values"]
            measurement["values"]["timestamp"] = timestamp_ms
            client.publish(topic, json.dumps(measurement["values"]))
        logger.info('Message published successfully.')
    except Exception as ex:
        logger.error('Exception in publishing message')
        logger.error(str(ex))
    
    return {"message": "Sensor data received"}