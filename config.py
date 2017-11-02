
# wifi configuration
WIFI_SSID = 'my_wifi_ssid'
WIFI_PASS = 'my_wifi_password'

# AWS general configuration
AWS_PORT = 8883
AWS_HOST = 'aws_host_url'
AWS_ROOT_CA = '/flash/cert/aws_root.ca'
AWS_CLIENT_CERT = '/flash/cert/aws_client.cert'
AWS_PRIVATE_KEY = '/flash/cert/aws_private.key'

################## Subscribe / Publish client #################
#CLIENT_ID = 'PycomPublishClient'
#TOPIC = 'PublishTopic'
#OFFLINE_QUEUE_SIZE = -1
#DRAINING_FREQ = 2
#CONN_DISCONN_TIMEOUT = 10
#MQTT_OPER_TIMEOUT = 5
#LAST_WILL_TOPIC = 'PublishTopic'
#LAST_WILL_MSG = 'To All: Last will message'

####################### Shadow updater ########################
#THING_NAME = "my thing name"
#CLIENT_ID = "ShadowUpdater"
#CONN_DISCONN_TIMEOUT = 10
#MQTT_OPER_TIMEOUT = 5

####################### Delta Listener ########################
#THING_NAME = "my thing name"
#CLIENT_ID = "DeltaListener"
#CONN_DISCONN_TIMEOUT = 10
#MQTT_OPER_TIMEOUT = 5

####################### Shadow Echo ########################
THING_NAME = "my thing name"
CLIENT_ID = "ShadowEcho"
CONN_DISCONN_TIMEOUT = 10
MQTT_OPER_TIMEOUT = 5
