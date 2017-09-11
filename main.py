from network import WLAN
from MQTT.uMQTTLib import AWSIoTMQTTClient
import machine
import time

WIFI_SSID = 'TNCAP204295'
WIFI_PASS = 'CC561B2F97'

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

topic="pythontest"
clientId="basicPubSub"
host='a15n3kcirh9jxj.iot.eu-west-1.amazonaws.com'
rootCAPath='/flash/cert/root-CA.crt'
certificatePath='/flash/cert/WindowsSample.cert.pem'
privateKeyPath='/flash/cert/WindowsSample.private.key'

#host='a20bylp0y1bcl1.iot.us-east-2.amazonaws.com'
#certificatePath='/flash/cert/ddd1b20d78-certificate.pem.crt'
#privateKeyPath='/flash/cert/ddd1b20d78-private.pem.key'

pycomAwsMQTTClient = AWSIoTMQTTClient(clientId)
pycomAwsMQTTClient.configureEndpoint(host, 8883)
pycomAwsMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

#pycomAwsMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
pycomAwsMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
pycomAwsMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
pycomAwsMQTTClient.configureConnectDisconnectTimeout(5)  # 10 sec
pycomAwsMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec
pycomAwsMQTTClient.configureLastWill(topic, 'To All: Last will message', 0)

if pycomAwsMQTTClient.connect():
    print('AWS connection succeeded')

pycomAwsMQTTClient.subscribe(topic, 1, customCallback)
time.sleep(2)

loopCount = 0
while loopCount < 8:
	pycomAwsMQTTClient.publish(topic, "New Message " + str(loopCount), 1)
	loopCount += 1
	time.sleep(7.0)
