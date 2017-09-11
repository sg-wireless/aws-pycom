import struct

# - Protocol types
MQTTv3_1 = 3
MQTTv3_1_1 = 4

# - OfflinePublishQueueing drop behavior
DROP_OLDEST = 0
DROP_NEWEST = 1

# Message types
MSG_CONNECT = 0x10
MSG_CONNACK = 0x20
MSG_PUBLISH = 0x30
MSG_PUBACK = 0x40
MSG_PUBREC = 0x50
MSG_PUBREL = 0x60
MSG_PUBCOMP = 0x70
MSG_SUBSCRIBE = 0x80
MSG_SUBACK = 0x90
MSG_UNSUBSCRIBE = 0xA0
MSG_UNSUBACK = 0xB0
MSG_PINGREQ = 0xC0
MSG_PINGRESP = 0xD0
MSG_DISCONNECT = 0xE0

class MQTTMessage:
    def __init__(self):
        self.timestamp = 0
        self.state = 0
        self.dup = False
        self.mid = 0
        self.topic = ""
        self.payload = None
        self.qos = 0
        self.retain = False

def _encode_16(x):
    return struct.pack("!H", x)

def _pascal_string(s):
    return struct.pack("!H", len(s)) + s

def _encode_varlen_length(length):
    i = 0
    buff = bytearray()
    while 1:
        buff.append(length % 128)
        length = length // 128
        if length > 0:
            buff[i] = buff[i] | 0x80
            i += 1
        else:
            break

    return buff

def _topic_matches_sub(sub, topic):
    result = True
    multilevel_wildcard = False

    slen = len(sub)
    tlen = len(topic)

    if slen > 0 and tlen > 0:
        if (sub[0] == '$' and topic[0] != '$') or (topic[0] == '$' and sub[0] != '$'):
            return False

    spos = 0
    tpos = 0

    while spos < slen and tpos < tlen:
        if sub[spos] == topic[tpos]:
            if tpos == tlen-1:
                # Check for e.g. foo matching foo/#
                if spos == slen-3 and sub[spos+1] == '/' and sub[spos+2] == '#':
                    result = True
                    multilevel_wildcard = True
                    break

            spos += 1
            tpos += 1

            if tpos == tlen and spos == slen-1 and sub[spos] == '+':
                spos += 1
                result = True
                break
        else:
            if sub[spos] == '+':
                spos += 1
                while tpos < tlen and topic[tpos] != '/':
                    tpos += 1
                if tpos == tlen and spos == slen:
                    result = True
                    break

            elif sub[spos] == '#':
                multilevel_wildcard = True
                if spos+1 != slen:
                    result = False
                    break
                else:
                    result = True
                    break

            else:
                result = False
                break

    if not multilevel_wildcard and (tpos < tlen or spos < slen):
        result = False

    return result
