import time
from simple import MQTTClient

DISCONNECTED = 0
CONNECTING = 1
CONNECTED = 2
DEVICE_ID = "pycom"
HOST = "a20bylp0y1bcl1.iot.us-east-2.amazonaws.com"
TOPIC_DOWNLOAD = "Download"
TOPIC_UPLOAD = "Upload"


state = DISCONNECTED
connection = None

def _recv_msg_callback(topic, msg):
    print("Received: {} from Topic: {}".format(msg, topic))

def _send_msg(msg):
    global connection
    connection.publish(TOPIC_UPLOAD, msg)

def run():
    global state
    global connection

    while True:
        # Wait for connection
        while state != CONNECTED:
            try:
                state = CONNECTING
                connection = MQTTClient(DEVICE_ID, HOST, port=8883)
                connection.connect(ssl=True, certfile='/flash/cert/pycom.cert.pem', keyfile='/flash/cert/pycom.private.key', ca_certs='/flash/cert/root-CA.crt')
                state = CONNECTED
            except:
                print('Error connecting to the server')
                time.sleep(0.5)
                continue

        print('Connected!')

        # Subscribe for messages
        connection.set_callback(_recv_msg_callback)
        connection.subscribe(TOPIC_DOWNLOAD)

        while state == CONNECTED:
            connection.check_msg()
            msg = '{"Name":"Pycom", "Data":"Test"}'
            print('Sending: ' + msg)
            _send_msg(msg)
            time.sleep(2.0)