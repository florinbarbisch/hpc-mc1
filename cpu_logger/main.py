from kafka import KafkaProducer
import os
import logging
import psutil
import time


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


topic = os.environ.get('KAFKA_TOPIC', "cpu-logger")
logger.info(f"Kafka topic: {topic}")

_producer = None
try:
    _producer = KafkaProducer(bootstrap_servers=os.environ.get('KAFKA_BROKER', 'broker1:9093').split(","), 
                              api_version=(0, 10),
                              max_block_ms=10000)
except Exception as ex:
    logger.error('Exception while connecting Kafka', exc_info=True)


while True:
    try:
        message = ','.join([str(p) for p in psutil.cpu_percent(interval=0, percpu=True)])
        value_bytes = bytes(message, encoding='utf-8')
        _producer.send(topic=topic, 
                       value=value_bytes)
        _producer.flush()
        logger.info('Message published successfully.')
    except Exception as ex:
        logger.error('Exception in publishing message', exc_info=True)

    time.sleep(0.5)
