from kafka import KafkaConsumer
from pymongo import MongoClient

import os
import logging
import time


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def deserialize_bytes(bytes_data):
    return {"cpu_percentages": [float(i) for i in bytes_data.decode('utf-8').split(',')]}

consumer = KafkaConsumer(os.environ.get('KAFKA_TOPIC', "cpu-logger"), 
                         auto_offset_reset = 'earliest',
                         bootstrap_servers = os.environ.get('KAFKA_BROKER', 'broker1:9093').split(","), 
                         group_id = os.environ.get('KAFKA_GROUP_ID', "cpu-logger-group"),
                         api_version = (0, 10), 
                         value_deserializer = deserialize_bytes,
                         max_poll_records = 50,
                         consumer_timeout_ms = 1000)


client = MongoClient(os.environ.get('MONGO_DB_CONNECTION_STRING'))
kafka_db = client["kafka"]  
cpu_logger_collection = kafka_db["cpu-logger"]

while True:
    try:
        messages = []
        for message in consumer:
            # this time.sleep call is to simulate a long running process (ML-model call, etc.)
            # I used this to test the consumer group functionality,
            # because the main goal of this module is not to develop methods that take a long time to execute.
            # But rather to show how to mitigate a bottleneck.
            time.sleep(float(os.environ.get('EXTRA_WAIT_TIME', 0)))
            cpu_logger_collection.insert_one({"cpu_percentages": sum(message.value["cpu_percentages"])/len(message.value["cpu_percentages"]),
                                              "timestamp": message.timestamp})
            logger.info("Inserted messages to MongoDB")
        # commit offsets so we won't get the same messages again
        consumer.commit()
    except Exception as ex:
        logger.error('Exception in consuming message', exc_info=True)

    time.sleep(0.5)