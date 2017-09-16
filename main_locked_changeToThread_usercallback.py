from network import WLAN
from MQTT.uMQTTLib import AWSIoTMQTTShadowClient
import machine
import time
import json

WIFI_SSID = 'TNCAP204295'
WIFI_PASS = 'CC561B2F97'

wlan = WLAN(mode=WLAN.STA)
wlan.connect(WIFI_SSID, auth=(None, WIFI_PASS), timeout=5000)
while not wlan.isconnected():
    machine.idle() # save power while waiting

print('WLAN connection succeeded!')

class shadowCallbackContainer:
	def __init__(self, deviceShadowInstance):
		self.deviceShadowInstance = deviceShadowInstance

	# Custom Shadow callback
	def customShadowCallback_Delta(self, payload, responseStatus, token):
		# payload is a JSON string ready to be parsed using json.loads(...)
		# in both Py2.x and Py3.x
		print("Received a delta message:")
		payloadDict = json.loads(payload)
		deltaMessage = json.dumps(payloadDict["state"])
		print(deltaMessage)
		print("Request to update the reported state...")
		newPayload = '{"state":{"reported":' + deltaMessage + '}}'
		self.deviceShadowInstance.shadowUpdate(newPayload, None, 5)
		print("Sent.")

thingName="WindowsSample"
clientId="basicShadowUpdater"
host='a15n3kcirh9jxj.iot.eu-west-1.amazonaws.com'
rootCAPath='/flash/cert/root-CA.crt'
certificatePath='/flash/cert/WindowsSample.cert.pem'
privateKeyPath='/flash/cert/WindowsSample.private.key'

pycomAwsMQTTShadowClient = AWSIoTMQTTShadowClient(clientId)
pycomAwsMQTTShadowClient.configureEndpoint(host, 8883)
pycomAwsMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

connected = pycomAwsMQTTShadowClient.connect()
if connected:
    print('AWS connection succeeded')

# Create a deviceShadow with persistent subscription
deviceShadowHandler = pycomAwsMQTTShadowClient.createShadowHandlerWithName(thingName, True)
shadowCallbackContainer_Bot = shadowCallbackContainer(deviceShadowHandler)

# Listen on deltas
deviceShadowHandler.shadowRegisterDeltaCallback(shadowCallbackContainer_Bot.customShadowCallback_Delta)

# Loop forever
while True:
	time.sleep(1)
