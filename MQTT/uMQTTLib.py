# import mqttCore
import MQTT.uMQTTClient as mqttClient
# import shadowManager
## import deviceShadow
#import AWSIoTPythonSDK.core.shadow.deviceShadow as deviceShadow
# Constants
# - Protocol types:
MQTTv3_1 = 3
MQTTv3_1_1 = 4
# - OfflinePublishQueueing drop behavior:
DROP_OLDEST = 0
DROP_NEWEST = 1
#

class AWSIoTMQTTClient:

    def __init__(self, clientID, protocolType=MQTTv3_1_1, cleanSession=True):
        self._mqttClient = mqttClient.MQTTClient(clientID, cleanSession, protocolType)

    # Configuration APIs
    #def configureLastWill(self, topic, payload, QoS):
        #self._mqttCore.setLastWill(topic, payload, QoS)

    #def clearLastWill(self):
        #self._mqttCore.clearLastWill()

    def configureEndpoint(self, hostName, portNumber):
        self._mqttClient.configEndpoint(hostName, portNumber)

    #def configureIAMCredentials(self, AWSAccessKeyID, AWSSecretAccessKey, AWSSessionToken=""):
        #self._mqttCore.configIAMCredentials(AWSAccessKeyID, AWSSecretAccessKey, AWSSessionToken)

    def configureCredentials(self, CAFilePath, KeyPath="", CertificatePath=""):  # Should be good for MutualAuth certs config and Websocket rootCA config
        self._mqttClient.configCredentials(CAFilePath, KeyPath, CertificatePath)

    #def configureAutoReconnectBackoffTime(self, baseReconnectQuietTimeSecond, maxReconnectQuietTimeSecond, stableConnectionTimeSecond):
    #    self._mqttCore.setBackoffTime(baseReconnectQuietTimeSecond, maxReconnectQuietTimeSecond, stableConnectionTimeSecond)

    #def configureOfflinePublishQueueing(self, queueSize, dropBehavior=DROP_NEWEST):
    #    self._mqttCore.setOfflinePublishQueueing(queueSize, dropBehavior)

    #def configureDrainingFrequency(self, frequencyInHz):
    #    self._mqttCore.setDrainingIntervalSecond(1/float(frequencyInHz))

    def configureConnectDisconnectTimeout(self, timeoutSecond):
        self._mqttClient.setConnectDisconnectTimeoutSecond(timeoutSecond)

    def configureMQTTOperationTimeout(self, timeoutSecond):
        self._mqttClient.setMQTTOperationTimeoutSecond(timeoutSecond)

    # MQTT functionality APIs
    def connect(self, keepAliveIntervalSecond=30):
        return self._mqttClient.connect(keepAliveIntervalSecond)

    #def disconnect(self):
        #return self._mqttCore.disconnect()

    def publish(self, topic, payload, QoS):
        return self._mqttClient.publish(topic, payload, QoS, False)  # Disable retain for publish by now

    def subscribe(self, topic, QoS, callback):
        return self._mqttClient.subscribe(topic, QoS, callback)

    #def unsubscribe(self, topic):
        #return self._mqttCore.unsubscribe(topic)


#class AWSIoTMQTTShadowClient:

#    def __init__(self, clientID, protocolType=MQTTv3_1_1, useWebsocket=False, cleanSession=True):
        # AWSIOTMQTTClient instance
#        self._AWSIoTMQTTClient = AWSIoTMQTTClient(clientID, protocolType, useWebsocket, cleanSession)
        # Configure it to disable offline Publish Queueing
#        self._AWSIoTMQTTClient.configureOfflinePublishQueueing(0)  # Disable queueing, no queueing for time-sentive shadow messages
#        self._AWSIoTMQTTClient.configureDrainingFrequency(10)
        # Now retrieve the configured mqttCore and init a shadowManager instance
#        self._shadowManager = shadowManager.shadowManager(self._AWSIoTMQTTClient._mqttCore)

    # Configuration APIs
#    def configureLastWill(self, topic, payload, QoS):
#        self._AWSIoTMQTTClient.configureLastWill(topic, payload, QoS)

#    def clearLastWill(self):
#        self._AWSIoTMQTTClient.clearLastWill()

#    def configureEndpoint(self, hostName, portNumber):
#        self._AWSIoTMQTTClient.configureEndpoint(hostName, portNumber)

#    def configureIAMCredentials(self, AWSAccessKeyID, AWSSecretAccessKey, AWSSTSToken=""):
        # AWSIoTMQTTClient.configureIAMCredentials
#        self._AWSIoTMQTTClient.configureIAMCredentials(AWSAccessKeyID, AWSSecretAccessKey, AWSSTSToken)

#    def configureCredentials(self, CAFilePath, KeyPath="", CertificatePath=""):  # Should be good for MutualAuth and Websocket
#        self._AWSIoTMQTTClient.configureCredentials(CAFilePath, KeyPath, CertificatePath)

#    def configureAutoReconnectBackoffTime(self, baseReconnectQuietTimeSecond, maxReconnectQuietTimeSecond, stableConnectionTimeSecond):
#        self._AWSIoTMQTTClient.configureAutoReconnectBackoffTime(baseReconnectQuietTimeSecond, maxReconnectQuietTimeSecond, stableConnectionTimeSecond)

#    def configureConnectDisconnectTimeout(self, timeoutSecond):
#        self._AWSIoTMQTTClient.configureConnectDisconnectTimeout(timeoutSecond)

#    def configureMQTTOperationTimeout(self, timeoutSecond):
#        self._AWSIoTMQTTClient.configureMQTTOperationTimeout(timeoutSecond)

    # Start the MQTT connection
#    def connect(self, keepAliveIntervalSecond=30):
#        return self._AWSIoTMQTTClient.connect(keepAliveIntervalSecond)

    # End the MQTT connection
#    def disconnect(self):
#        return self._AWSIoTMQTTClient.disconnect()

    # Shadow management API
#    def createShadowHandlerWithName(self, shadowName, isPersistentSubscribe):
        # Create and return a deviceShadow instance
#        return deviceShadow.deviceShadow(shadowName, isPersistentSubscribe, self._shadowManager)
        # Shadow APIs are accessible in deviceShadow instance":
        ###
        # deviceShadow.shadowGet
        # deviceShadow.shadowUpdate
        # deviceShadow.shadowDelete
        # deviceShadow.shadowRegisterDelta
        # deviceShadow.shadowUnregisterDelta

    # MQTT connection management API
#    def getMQTTConnection(self):

        # Return the internal AWSIoTMQTTClient instance
#        return self._AWSIoTMQTTClient
