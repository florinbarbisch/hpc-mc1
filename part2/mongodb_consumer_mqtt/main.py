import paho.mqtt.subscribe as subscribe
import uuid
from pymongo import MongoClient
import os
import logging
import time


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


client = MongoClient(os.environ.get('MONGO_DB_CONNECTION_STRING'))
mqtt_db = client["mqtt"]
cpu_logger_collection = mqtt_db["cpu-logger"]


def on_message(client, userdata, message):
    percentages = [float(x) for x in message.payload.decode('utf-8').split(',')]
    cpu_logger_collection.insert_one({"cpu_percentages": sum(percentages)/len(percentages),
                                      "timestamp": time.time()})
    logger.info("Inserted message to MongoDB")


subscribe.callback(on_message, 
                   os.environ.get('MQTT_TOPIC', "cpu/percent"), 
                   hostname=os.environ.get('MQTT_BROKER', "mosquitto1"), 
                   client_id="mongodb-subsrciber-" + str(uuid.uuid4()))