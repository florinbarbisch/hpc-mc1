import paho.mqtt.client as mqtt
import uuid
import os
import logging
import psutil
import time


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


topic = os.environ.get('MQTT_TOPIC', "cpu/percent")
logger.info(f"MQTT topic: {topic}")


client = mqtt.Client(client_id="cpu-logger-" + str(uuid.uuid4()))
client.loop_start()


try:
    client.connect(os.environ.get('MQTT_BROKER', "mosquitto1"))
except Exception as ex:
    logger.error('Exception while connecting to MQTT Broker', exc_info=True)


while True:
    try:
        percentages = psutil.cpu_percent(interval=0, percpu=True)
        client.publish(topic, ','.join([str(p) for p in percentages]))
        logger.info('Message published successfully.')
    except Exception as ex:
        logger.error('Exception in publishing message', exc_info=True)

    time.sleep(0.5)
