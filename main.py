from network import WLAN
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import machine
import time
import json

WIFI_SSID = 'your wifi ssid'
WIFI_PASS = 'your wifi password'

wlan = WLAN(mode=WLAN.STA)
wlan.connect(WIFI_SSID, auth=(None, WIFI_PASS), timeout=5000)
while not wlan.isconnected():
    machine.idle() # save power while waiting

print('WLAN connection succeeded!')

# Custom Shadow callback
def customShadowCallback_Update(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    if responseStatus == "timeout":
        print("Update request " + token + " time out!")
    if responseStatus == "accepted":
        payloadDict = json.loads(payload)
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print("Update request with token: " + token + " accepted!")
        print("property: " + str(payloadDict["state"]["desired"]["property"]))
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")

def customShadowCallback_Delete(payload, responseStatus, token):
    if responseStatus == "timeout":
        print("Delete request " + token + " time out!")
    if responseStatus == "accepted":
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print("Delete request with token: " + token + " accepted!")
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    if responseStatus == "rejected":
        print("Delete request " + token + " rejected!")

thingName="your thing name"
clientId="your client Id"
host='your host name'
rootCAPath='path to you root CA'
certificatePath='path to your public key'
privateKeyPath='path to your private key'

pycomAwsMQTTShadowClient = AWSIoTMQTTShadowClient(clientId)
pycomAwsMQTTShadowClient.configureEndpoint(host, 8883)
pycomAwsMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTShadowClient configuration
pycomAwsMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
pycomAwsMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
pycomAwsMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect to AWS IoT
connected = pycomAwsMQTTShadowClient.connect()
if connected:
    print('AWS connection succeeded')

deviceShadowHandler = pycomAwsMQTTShadowClient.createShadowHandlerWithName(thingName, True)

# Delete shadow JSON doc
deviceShadowHandler.shadowDelete(customShadowCallback_Delete, 5)

# Update shadow in a loop
loopCount = 0
while True:
    JSONPayload = '{"state":{"desired":{"property":' + str(loopCount) + '}}}'
    deviceShadowHandler.shadowUpdate(JSONPayload, customShadowCallback_Update, 5)
    loopCount += 1
    time.sleep(2)
