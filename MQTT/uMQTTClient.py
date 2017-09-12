import MQTT.uMQTTMsg as mqttMsg
import socket
import ssl
import _thread
import time
import struct
import select

class MQTTClient:

    # Connection state
    STATE_CONNECTED = 0x01
    STATE_CONNECTING = 0x02
    STATE_DISCONNECTED = 0x03

    def __init__(self, clientID, cleanSession, protocol):
        self.client_id = clientID
        self._cleanSession = cleanSession
        self._protocol = protocol
        self._userdata = None
        self._host = ""
        self._port = -1
        self._cafile = ""
        self._key = ""
        self._cert = ""
        self._sock = None
        self._user = ""
        self._password = ""
        self._keepAliveInterval = 60
        self._will = False
        self._will_topic = ""
        self._will_message= None
        self._will_qos = 0
        self._will_retain = False
        self._out_packet_mutex=_thread.allocate_lock()
        self._output_queue=[]
        self._output_queue_size=-1
        self._output_queue_dropbehavior=-1
        _thread.stack_size(6144)
        _thread.start_new_thread(self._io_thread_func,())
        self._connection_state = self.STATE_DISCONNECTED
        self._connectdisconnectTimeout = 30
        self._mqttOperationTimeout = 5
        self._conn_state_mutex=_thread.allocate_lock()
        self._topic_callback_queue=[]
        self._callback_mutex=_thread.allocate_lock()
        self._pid = 0
        self._subscribeSent = False
        self._unsubscribeSent = False
        self._poll = select.poll()
        self._receive_timeout=3000
        self._pingSent=False
        self._ping_interval=20
        self._waiting_ping_resp=False
        self._ping_cutoff=3
        self._baseReconnectTimeSecond=1
        self._maximumReconnectTimeSecond=32
        self._minimumConnectTimeSecond=20
        self._draining_interval=2
        self._draining_cutoff=3

    def configEndpoint(self, srcHost, srcPort):
        self._host = srcHost
        self._port = srcPort

    def configCredentials(self, srcCAFile, srcKey, srcCert):
        self._cafile = srcCAFile
        self._key = srcKey
        self._cert = srcCert

    def setConnectDisconnectTimeoutSecond(self, srcConnectDisconnectTimeout):
        self._connectdisconnectTimeout = srcConnectDisconnectTimeout

    def setMQTTOperationTimeoutSecond(self, srcMQTTOperationTimeout):
        self._mqttOperationTimeout = srcMQTTOperationTimeout

    def clearLastWill(self):
        self._will = False
        self._will_topic = ""
        self._will_message= None
        self._will_qos = 0
        self._will_retain = False

    def setLastWill(self, topic, payload=None, QoS=0, retain=False):
        self._will=True
        self._will_qos = QoS
        self._will_retain = retain
        self._will_topic = topic.encode('utf8')

        if isinstance(payload, bytearray):
            self._will_message=payload
        elif isinstance(payload, str):
            self._will_message=payload.encode('utf8')
        elif isinstance(payload, int) or isinstance(payload, float):
            self._will_message=str(payload)

    def configIAMCredentials(self, srcAWSAccessKeyID, srcAWSSecretAccessKey, srcAWSSessionToken):
        raise NotImplementedError ('Websockets not supported')

    def setOfflinePublishQueueing(self, srcQueueSize, srcDropBehavior):
        if srcDropBehavior != mqttMsg.DROP_OLDEST and srcDropBehavior != mqttMsg.DROP_NEWEST:
            raise ValueError("Invalid packet drop behavior")

        self._output_queue_size=srcQueueSize
        self._output_queue_dropbehavior=srcDropBehavior

    def setDrainingIntervalSecond(self, srcDrainingIntervalSecond):
        self._draining_interval=srcDrainingIntervalSecond

    def setBackoffTiming(self, srcBaseReconnectTimeSecond, srcMaximumReconnectTimeSecond, srcMinimumConnectTimeSecond):
        self._baseReconnectTimeSecond=srcBaseReconnectTimeSecond
        self._maximumReconnectTimeSecond=srcMaximumReconnectTimeSecond
        self._minimumConnectTimeSecond=srcMinimumConnectTimeSecond

    def connect(self, keepAliveInterval=30):
        self._keepAliveInterval = keepAliveInterval
        self._conn_state_mutex.acquire()
        self._connection_state = self.STATE_CONNECTING
        self._conn_state_mutex.release()
        try:
            if self._sock:
                self._poll.unregister(self._sock)
                self._sock.close()
                self._sock = None

            self._sock = socket.socket()
            if self._cafile:
                self._sock = ssl.wrap_socket(
                    self._sock,
                    certfile=self._cert,
                    keyfile=self._key,
                    ca_certs=self._cafile,
                    cert_reqs=ssl.CERT_REQUIRED)

            self._sock.connect(socket.getaddrinfo(self._host, self._port)[0][-1])
            self._poll.register(self._sock, select.POLLIN)
        except socket.error as err:
            print("Socket create error: {0}".format(err))

            self._conn_state_mutex.acquire()
            self._connection_state = self.STATE_DISCONNECTED
            self._conn_state_mutex.release()

            return False
        self._send_connect(self._keepAliveInterval, self._cleanSession)

        # delay to check the state
        count_10ms = 0
        while(count_10ms <= self._connectdisconnectTimeout * 100 and self._connection_state != self.STATE_CONNECTED):
            count_10ms += 1
            time.sleep(0.01)

        return True if self._connection_state == self.STATE_CONNECTED else False

    def subscribe(self, topic, qos, callback):
        if (topic is None or callback is None):
            raise TypeError("Invalid subscribe values.")

        topic = topic.encode('utf8')
        pkt_len = 2 + 2 + len(topic) + 1 # packet identifier + len of topic (16 bits) + topic len + QOS

        self._pid += 1
        pkt = bytearray([0x82])
        pkt.extend(mqttMsg._encode_varlen_length(pkt_len)) # len of the remaining
        pkt.extend(mqttMsg._encode_16(self._pid))
        pkt.extend(mqttMsg._pascal_string(topic))
        pkt.append(qos)

        self._subscribeSent = False
        self._push_on_send_queue(pkt)

        count_10ms = 0
        while(count_10ms <= self._mqttOperationTimeout * 100 and not self._subscribeSent):
            count_10ms += 1
            time.sleep(0.01)

        if self._subscribeSent:
            self._callback_mutex.acquire()
            self._topic_callback_queue.append((topic, callback))
            self._callback_mutex.release()
            return True

        return False

    def publish(self, topic, payload, qos, retain, dup=False):

        topic = topic.encode('utf8')
        hdr = 0x30 | (dup << 3) | (qos << 1) | retain
        pkt_len = (2 + len(topic) +
                    (2 if qos else 0) +
                    (len(payload)))

        pkt = bytearray()
        pkt.append(hdr)
        pkt.extend(mqttMsg._encode_varlen_length(pkt_len)) # len of the remaining
        pkt.extend(mqttMsg._pascal_string(topic))
        if qos:
            self._pid += 1 #todo: I don't think this is the way to deal with the packet id
            pkt.extend(mqttMsg._encode_16(self._pid))

        self._push_on_send_queue(pkt)
        self._push_on_send_queue(payload)

    def _remove_topic_callback(self, topic):
        deleted=False

        self._callback_mutex.acquire()
        for i in range(0, len(self._topic_callback_queue)):
            if self._topic_callback_queue[i][0] == topic:
                self._topic_callback_queue.pop(i)
                deleted=True
        self._callback_mutex.release()

        return deleted

    def unsubscribe(self, topic):

        self._unsubscribeSent = False
        self._send_unsubscribe(topic, False)

        count_10ms = 0
        while(count_10ms <= self._mqttOperationTimeout * 100 and not self._unsubscribeSent):
            count_10ms += 1
            time.sleep(0.01)

        if self._unsubscribeSent:
            topic = topic.encode('utf8')
            return self._remove_topic_callback(topic)

        return False

    def disconnect(self):

        pkt = struct.pack('!BB', mqttMsg.MSG_DISCONNECT, 0)
        self._push_on_send_queue(pkt)

        time.sleep(self._connectdisconnectTimeout)

        if self._sock:
            self._sock.close()
            self._sock = None

        return True

    def _send_connect(self, keepalive, clean_session):

        pkt_len = (12 + len(self.client_id) + # 10 + 2 + len(client_id)
                    (2 + len(self._user) if self._user else 0) +
                    (2 + len(self._password) if self._password else 0))

        flags = (0x80 if self._user else 0x00) | (0x40 if self._password else 0x00) | (0x02 if clean_session else 0x00)

        if self._will_message:
            flags |= (self._will_retain << 3 | self._will_qos << 1 | 1) << 2
            pkt_len += 4 + len(self._will_topic) + len(self._will_message)

        pkt = bytearray([mqttMsg.MSG_CONNECT]) # connect
        pkt.extend(mqttMsg._encode_varlen_length(pkt_len)) # len of the remaining
        pkt.extend(b'\x00\x04MQTT\x04') # len of "MQTT" (16 bits), protocol name, and protocol version
        pkt.append(flags)
        pkt.extend(b'\x00\x00') # disable keepalive
        pkt.extend(mqttMsg._pascal_string(self.client_id))
        if self._will_message:
            pkt.extend(mqttMsg._pascal_string(self._will_topic))
            pkt.extend(mqttMsg._pascal_string(self._will_message))
        if self._user:
            pkt.extend(mqttMsg._pascal_string(self._user))
        if self._password:
            pkt.extend(mqttMsg._pascal_string(self._password))

        return self._push_on_send_queue(pkt, True)

    def _send_unsubscribe(self, topic, dup=False):

        pkt = bytearray()
        msg_type = mqttMsg.MSG_UNSUBSCRIBE | (dup<<3) | (1<<1)
        pkt.extend(struct.pack("!B", msg_type))

        remaining_length = 2 + 2 + len(topic)
        pkt.extend(mqttMsg._encode_varlen_length(remaining_length))

        self._pid += 1
        pkt.extend(mqttMsg._encode_16(self._pid))
        pkt.extend(mqttMsg._pascal_string(topic))

        return self._push_on_send_queue(pkt)

    def _send_puback(self, msg_id):

        remaining_length = 2
        pkt = struct.pack('!BBH', mqttMsg.MSG_PUBACK, remaining_length, msg_id)

        return self._push_on_send_queue(pkt)

    def _send_pubrec(self, msg_id):

        remaining_length = 2
        pkt = struct.pack('!BBH', mqttMsg.MSG_PUBREC, remaining_length, msg_id)

        return self._push_on_send_queue(pkt)

    def _send_pingreq(self):
        pkt = struct.pack('!BB', mqttMsg.MSG_PINGREQ, 0)
        return self._push_on_send_queue(pkt, True)

    def _drop_message(self):

        if self._output_queue_size == -1:
            return False
        elif self._output_queue_size == 0:
            return True
        else:
            return True if len(self._output_queue) >= self._output_queue_size else False

    def _push_on_send_queue(self, packet,prioritize=False):
        succeded = False

        if self._drop_message():
            if self._output_queue_dropbehavior == mqttMsg.DROP_OLDEST:
                self._out_packet_mutex.acquire()
                if self._out_packet_mutex.locked():
                    self._output_queue.pop(0)
                self._out_packet_mutex.release()
            else:
                return False

        self._out_packet_mutex.acquire()
        if self._out_packet_mutex.locked():
            if prioritize:
                self._send_packet(packet);
            else:
                self._output_queue.append(packet)
            succeded = True
        self._out_packet_mutex.release()

        return succeded

    def _parse_connack(self, payload):

        if len(payload) != 2:
            return False

        (flags, result) = struct.unpack("!BB", payload)

        if result == 0:
            self._conn_state_mutex.acquire()
            self._connection_state = self.STATE_CONNECTED
            self._conn_state_mutex.release()
            return True
        else:
            self._conn_state_mutex.acquire()
            self._connection_state = mqttMsg.STATE_DISCONNECTED
            self._conn_state_mutex.release()
            return False

    def _parse_suback(self, payload):
        self._subscribeSent = True
        print('Subscribed to topic')

        # VIMP check below
        #assert resp[0] == 0x90
        #assert resp[2] == pkt[2] and resp[3] == pkt[3]
        #if resp[4] == 0x80:
        #    raise MQTTException(resp[4])

        return True

    def _parse_puback(self, payload):
        return True

    def _notify_message(self, message):
        notified = False
        self._callback_mutex.acquire()
        for t_obj in self._topic_callback_queue:
            if mqttMsg._topic_matches_sub(t_obj[0], message.topic):
                t_obj[1](self, self._userdata, message)
                notified = True
        self._callback_mutex.release()

        return notified

    def _parse_publish(self, cmd, packet):

        msg = mqttMsg.MQTTMessage()
        msg.dup = (cmd & 0x08)>>3
        msg.qos = (cmd & 0x06)>>1
        msg.retain = (cmd & 0x01)

        pack_format = "!H" + str(len(packet)-2) + 's'
        (slen, packet) = struct.unpack(pack_format, packet)
        pack_format = '!' + str(slen) + 's' + str(len(packet)-slen) + 's'
        (msg.topic, packet) = struct.unpack(pack_format, packet)

        if len(msg.topic) == 0:
            return False

        if msg.qos > 0:
            pack_format = "!H" + str(len(packet)-2) + 's'
            (msg.mid, packet) = struct.unpack(pack_format, packet)

        msg.payload = packet

        if msg.qos == 0:
            self._notify_message(msg)
        elif msg.qos == 1:
            self._send_puback(msg.mid)
            self._notify_message(msg)
        elif msg.qos == 2:
            self._send_pubrec(msg.mid)
            self._notify_message(msg)
        else:
            return False

        return True

    def _parse_unsuback(self, payload):
        self._unsubscribeSent = True
        return True

    def _parse_pingresp(self):
        self._pingSent = True
        return True

    def _parse_packet(self, cmd, payload):
        msg_type = cmd & 0xF0

        if msg_type == mqttMsg.MSG_CONNACK:
            return self._parse_connack(payload)
        elif msg_type == mqttMsg.MSG_SUBACK:
            return self._parse_suback(payload)
        elif msg_type == mqttMsg.MSG_PUBACK:
            return self._parse_puback(payload)
        elif msg_type == mqttMsg.MSG_PUBLISH:
            return self._parse_publish(cmd, payload)
        elif msg_type == mqttMsg.MSG_UNSUBACK:
            return self._parse_unsuback(payload)
        elif msg_type == mqttMsg.MSG_PINGRESP:
            return self._parse_pingresp()
        else:
            print('Unknown message type: %d' % msg_type)
            return False

    def _receive_packet(self):

        if not self._poll.poll(self._receive_timeout):
            return False

        # Read message type
        try:
            self._sock.setblocking(False)
            msg_type = self._sock.recv(1)
        except socket.error as err:
            print("Socket receive error: {0}".format(err))
            return False
        else:
            if len(msg_type) == 0:
                return False
            msg_type = struct.unpack("!B", msg_type)[0]
            self._sock.setblocking(True)

        # Read payload length
        multiplier = 1
        bytes_read = 0
        bytes_remaining = 0
        while True:
            try:
                if self._sock:
                    byte = self._sock.recv(1)
            except socket.error as err:
                print("Socket receive error: {0}".format(err))
                return False
            else:
                bytes_read = bytes_read + 1
                if bytes_read > 4:
                    return False

                byte = struct.unpack("!B", byte)[0]
                bytes_remaining +=  (byte & 127) * multiplier
                multiplier += 128

            if (byte & 128) == 0:
                break

        # Read payload
        try:
            if self._sock:
                if bytes_remaining > 0:
                    payload = self._sock.recv(bytes_remaining)
                else:
                    payload = b''
        except socket.error as err:
                print("Socket receive error: {0}".format(err))
                return False

        return self._parse_packet(msg_type, payload)

    def _send_packet(self, packet):
        written = -1
        try:
            if self._sock:
                written = self._sock.write(packet)
                print('Packet sent. (Length: %d)' % written)
        except socket.error as err:
            print('Socket send error {0}'.format(err))
            return False

        return True if len(packet) == written else False

    def _verify_connection_state(self):

        elapsed = time.time() - self._start_time
        if not self._waiting_ping_resp and elapsed > self._ping_interval:
            if self._connection_state == self.STATE_CONNECTED:
                self._pingSent=False
                self._send_pingreq()
                self._waiting_ping_resp=True
            elif self._connection_state == self.STATE_DISCONNECTED:
                self.connect()

            self._start_time = time.time()
        elif self._waiting_ping_resp and (self._connection_state == self.STATE_CONNECTED or elapsed > self._mqttOperationTimeout):
            if not self._pingSent:
                if self._ping_failures <= self._ping_cutoff:
                    self._ping_failures+=1
                else:
                    self.connect()
            else:
                self._ping_failures=0

            self._start_time = time.time()
            self._waiting_ping_resp=False

    def _io_thread_func(self):
        time.sleep(5.0)

        self._start_time = time.time()
        self._ping_failures=0
        while True:

            self._verify_connection_state()

            self._out_packet_mutex.acquire()
            if self._out_packet_mutex.locked() and len(self._output_queue) > 0:
                packet=self._output_queue[0]
                if self._send_packet(packet):
                    self._output_queue.pop(0)
            self._out_packet_mutex.release()

            print('Queue Size: %d' % len(self._output_queue))

            self._receive_packet()

            if len(self._output_queue) >= self._draining_cutoff:
                time.sleep(self._draining_interval)
