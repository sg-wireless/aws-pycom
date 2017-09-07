from network import WLAN
from MQTT.uMQTTLib import AWSIoTMQTTClient

import machine
import time

WIFI_SSID = 'your ssid'
WIFI_PASS = 'your pass'

wlan = WLAN(mode=WLAN.STA)
wlan.connect(WIFI_SSID, auth=(None, WIFI_PASS), timeout=5000)
while not wlan.isconnected():
    machine.idle() # save power while waiting

print('WLAN connection succeeded!')

def customCallback(client, userdata, message):
	print("Received a new message: ")
	print(message.payload)
	print("from topic: ")
	print(message.topic)
	print("--------------\n\n")

clientId="basicPubSub"
host='a15n3kcirh9jxj.iot.eu-west-1.amazonaws.com'
rootCAPath='/flash/root-CA.crt'
certificatePath='/flash/WindowsSample.cert.pem'
privateKeyPath='/flash/WindowsSample.private.key'

pycomAwsMQTTClient = AWSIoTMQTTClient(clientId)
pycomAwsMQTTClient.configureEndpoint(host, 8883)
pycomAwsMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

#pycomAwsMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
#pycomAwsMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
#pycomAwsMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
pycomAwsMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
pycomAwsMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec


if pycomAwsMQTTClient.connect():
    print('AWS connection succeeded')

topic="a topic"
pycomAwsMQTTClient.subscribe(topic, 1, customCallback)
time.sleep(2)

loopCount = 0
while True:
	pycomAwsMQTTClient.publish(topic, "New Message " + str(loopCount), 1)
	loopCount += 1
	time.sleep(10.0)
