from kafka import KafkaConsumer, KafkaProducer
import json
import os
import logging
import time
import multiprocessing
from scipy.fft import fft

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def consume_messages(pipe_connection):
    logger.info("Starting consumer")

    consumer = KafkaConsumer(os.environ.get('KAFKA_CONSUMER_TOPIC', "accelerometer"), 
                             auto_offset_reset = 'earliest',
                             bootstrap_servers = os.environ.get('KAFKA_BROKER', 'broker1:9093').split(","), 
                             group_id = os.environ.get('KAFKA_GROUP_ID', "accelerometer-group"),
                             api_version = (0, 10), 
                             value_deserializer = json.loads,
                             consumer_timeout_ms = 1000)
    logger.info("Consumer started")

    messages_by_key = {}
    
    count = 0
    last_ordering = 0
    while True:
        # Step 1: Consume messages
        try:
            for message in consumer:
                if count == 0:
                    logger.info(f"Received first message: {message}")
                # convert bytes to string
                key = message.key.decode('utf-8')
                if key not in messages_by_key:
                    # add a mulltiprocessing.Dictionary to the dictionary
                    messages_by_key[key] = {}
                    
                messages_current_key = messages_by_key[key]

                seconds = int(message.timestamp / 1000)
                if seconds not in messages_current_key:
                    # add a mulltiprocessing.Queue for each second
                    messages_current_key[seconds] = []

                messages_current_key_seconds = messages_current_key[seconds]

                messages_current_key_seconds.append([
                    message.timestamp, 
                    message.value.get('x'),
                    message.value.get('y'), 
                    message.value.get('z')
                    ])

                if count % 100 == 0:
                    logger.info(f"Received {count} messages")
                count += 1
                
                # order every 100 messages
                if count-100 >= last_ordering:
                    # Step 2: Order messages and send to pipe
                    for key in messages_by_key:
                        messages_current_key = messages_by_key[key]
                        seconds = list(messages_current_key.keys())
                        # only process the first n-1 seconds
                        for second in seconds[:-1]:
                            messages_current_key_seconds = messages_current_key[second]
                            messages_current_key_seconds.sort(key=lambda x: x[0])
                            # send the messages to the pipe
                            pipe_connection.send({
                                'key': key,
                                'second': second,
                                'x': [x[1] for x in messages_current_key_seconds],
                                'y': [x[2] for x in messages_current_key_seconds],
                                'z': [x[3] for x in messages_current_key_seconds]
                            })
                            # remove the messages from the dictionary
                            del messages_current_key[second]
                    last_ordering = count
                    # commit offsets so we won't get the same messages again
                    consumer.commit()
        except Exception as ex:
            logger.error(f"Error consuming messages: {ex}")
        time.sleep(0.05)


def complex_ndarray_to_list(complex_ndarray):
    return [complex_ndarray.real.tolist(), complex_ndarray.imag.tolist()]

def process_messages(pipe_connection):
    producer = KafkaProducer(bootstrap_servers=os.environ.get('KAFKA_BROKER', 'broker1:9093').split(","), 
                              api_version=(0, 10),
                              max_block_ms=10000)
    # poll the pipe for messages and compute the fft
    while True:
        message = pipe_connection.recv()
        key = message['key']
        second = message['second']
        
        # compute the fft
        x_fft = fft(message['x'])
        y_fft = fft(message['y'])
        z_fft = fft(message['z'])
        # order these arrays by the absolute value of the complex number
        x_fft = x_fft[abs(x_fft).argsort(kind='heapsort')]
        y_fft = y_fft[abs(y_fft).argsort(kind='heapsort')]
        z_fft = z_fft[abs(z_fft).argsort(kind='heapsort')]
        # send the fft to the producer
        message = {
                    'second': second,
                    'x': complex_ndarray_to_list(x_fft),
                    'y': complex_ndarray_to_list(y_fft),
                    'z': complex_ndarray_to_list(z_fft)
            }
        producer.send(os.environ.get('KAFKA_PRODUCER_TOPIC', "accelerometer-fft"),
                        key=key.encode('utf-8'),
                        value=bytes(json.dumps(message), encoding='utf-8'))
        producer.flush()

        logger.info(f"Processed messages for key {key} and second {second}")


# start two processes, one for consuming messages and one for processing messages

# create a pipe to communicate between the processes
pipe_end, pipe_start = multiprocessing.Pipe()

p1 = multiprocessing.Process(target=consume_messages, args=(pipe_end,))
p2 = multiprocessing.Process(target=process_messages, args=(pipe_start,))
p1.start()
p2.start()
p1.join()
p2.join()