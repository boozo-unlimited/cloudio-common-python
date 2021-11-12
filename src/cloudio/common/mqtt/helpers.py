# -*- coding: utf-8 -*-

import logging
import os
import ssl
import time
import traceback
import uuid
import json
from abc import ABCMeta
from threading import Thread, RLock, Event, current_thread

import paho.mqtt.client as mqtt  # pip install paho-mqtt
from cloudio.common.utils import path_helpers

from .pending_update import PendingUpdate

# Set logging level
logging.getLogger('cloudio.mqttasyncclient').setLevel(logging.INFO)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
logging.getLogger('cloudio.mqttreconnectclient').setLevel(logging.INFO)  # DEBUG, INFO, WARNING, ERROR, CRITICAL


class MqttAsyncClient(object):
    """Mimic the behavior of the java.MqttAsyncClient class"""

    # Errors from mqtt module - mirrored into this class
    MQTT_ERR_SUCCESS = mqtt.MQTT_ERR_SUCCESS
    MQTT_ERR_NO_CONN = mqtt.MQTT_ERR_NO_CONN
    MQTT_ERR_INVAL = mqtt.MQTT_ERR_INVAL

    log = logging.getLogger('cloudio.mqttasyncclient')

    def __init__(self, host, client_id='', clean_session=True):
        self._is_connected = False
        self._host = host
        self._on_connect_callback = None
        self._on_disconnect_callback = None
        self._on_message_published_callback = None
        self._on_message_callback = None
        self._client = None
        self._client_lock = RLock()  # Protects access to _client attribute

        # Store mqtt client parameter for potential later reconnection
        # to cloud.iO
        self._client_client_id = client_id
        self._client_clean_session = clean_session

    def _create_mqtt_client(self):
        self._client_lock.acquire()
        if self._client is None:
            if self._client_client_id:
                self._client = mqtt.Client(client_id=self._client_client_id,
                                           clean_session=self._client_clean_session)
            else:
                self._client = mqtt.Client()

            self._client.on_connect = self.on_connect
            self._client.on_disconnect = self.on_disconnect
            self._client.on_message = self.on_message
            self._client.on_publish = self.on_published
        self._client_lock.release()

    def set_on_connect_callback(self, on_connect_callback):
        self._on_connect_callback = on_connect_callback

    def set_on_disconnect_callback(self, on_disconnect_callback):
        self._on_disconnect_callback = on_disconnect_callback

    def set_on_message_callback(self, on_message_callback):
        self._on_message_callback = on_message_callback

    def set_on_message_published(self, on_message_published_callback):
        self._on_message_published_callback = on_message_published_callback

    def connect(self, options):
        port = options.port if options.port else 1883  # Default port without ssl

        if options.ca_file:
            # Check if file exists
            if not os.path.isfile(options.ca_file):
                raise RuntimeError('CA file \'%s\' does not exist!' % options.ca_file)

        client_cert_file = None
        if options.client_cert_file:
            # Check if file exists
            if not os.path.isfile(options.client_cert_file):
                raise RuntimeError('Client certificate file \'%s\' does not exist!' % options.client_cert_file)
            else:
                client_cert_file = options.client_cert_file

        client_key_file = None
        if options.client_key_file:
            # Check if file exists
            if not os.path.isfile(options.client_key_file):
                raise RuntimeError('Client private key file \'%s\' does not exist!' % options.client_key_file)
            else:
                client_key_file = options.client_key_file

        # get the json certification file
        jsonCert_file = None
        if options.jsonCerts:
            # Check if file exists
            if not os.path.isfile(options.jsonCerts):
                raise RuntimeError('Json certs file \'%s\' does not exist!' % options.jsonCerts)
            else:
                dirname = 'Cloud.io_temp'

                # read the json certificates and key file
                jsonCert_file = open(options.jsonCerts)

                jdata = json.load(jsonCert_file)

                # get the certificate and key
                caCert = jdata['caCertificate']
                clientCert = jdata['clientCertificate']
                clientKey = jdata['clientPrivateKey']

                # create the directory if not exist
                if not os.path.exists(dirname):
                    os.mkdir(dirname)

                # write certificate and keys in a separate file
                caCertF = open(dirname + "/caCert.pem", "w+")
                caCertF.seek(0)
                caCertF.writelines(caCert)
                caCertF.truncate()
                caCertF.close()

                clientCertF = open(dirname + "/clientCert.pem", "w+")
                clientCertF.seek(0)
                clientCertF.writelines(clientCert)
                clientCertF.truncate()
                clientCertF.close()

                clientKeyF = open(dirname + "/clientKey.pem", "w+")
                clientKeyF.seek(0)
                clientKeyF.writelines(clientKey)
                clientKeyF.truncate()
                clientKeyF.close()

                # save the certificates and key files
                client_key_file = dirname + "/clientKey.pem"
                client_cert_file = dirname + "/clientCert.pem"
                options.ca_file = dirname + "/caCert.pem"

        # Check which TSL protocol version should be used
        try:
            tls_version = ssl.PROTOCOL_TLSv1_2
        except Exception:  # pragma: no cover
            tls_version = ssl.PROTOCOL_TLSv1  # pragma: no cover
        if options.tls_version:
            if options.tls_version.lower() in ('tlsv1', 'tlsv1.0'):
                tls_version = ssl.PROTOCOL_TLSv1

        self._client_lock.acquire()  # Protect _client attribute

        # Create MQTT client if necessary
        self._create_mqtt_client()

        if options.will:
            self._client.will_set(options.will['topic'],
                                  options.will['message'],
                                  options.will['qos'],
                                  options.will['retained'])
        if self._client:
            if options.ca_file:
                port = options.port if options.port else 8883  # Default port with ssl
                self._client.tls_set(options.ca_file,  # CA certificate
                                     certfile=client_cert_file,  # Client certificate
                                     keyfile=client_key_file,  # Client private key
                                     tls_version=tls_version,  # ssl.PROTOCOL_TLSv1, ssl.PROTOCOL_TLSv1_2
                                     ciphers=None)  # None, 'ALL', 'TLSv1.2', 'TLSv1.0'
                self._client.tls_insecure_set(True)  # True: No verification of the server hostname in
                # the server certificate
            else:
                self.log.error('No CA file provided. Connection attempt likely to fail!')

            # Check if username and password is provided
            if options.username:
                password = options.password
                if not options.password:
                    # paho client v1.3 and higher do no more accept '' as empty string. Need None
                    password = None
                self._client.username_pw_set(options.username, password=password)

            self._client_lock.release()  # Need to release lock before connect().
            # Otherwise other thread cannot disconnect

            # Let MQTT client do the connection
            self._client.connect(self._host, port=port)
            if self._client:
                self._client.loop_start()

    def disconnect(self, force_client_disconnect=True):
        """Disconnects MQTT client

        In case to let MQTT client die silently, call force_client_disconnect parameter with
        'false' value. In this case no disconnect callback method is called.

        ::param force_client_disconnect Set to true to call also MQTT clients disconnect method. Default: true
        :type force_client_disconnect bool
        :return None
        :rtype: None
        """
        self._client_lock.acquire()
        # Stop MQTT client if still running
        if self._client:
            if force_client_disconnect:
                self._client.on_disconnect = None  # Want get a disconnect callback call
                self._client.disconnect()
            self._client.loop_stop()
            self._client = None

        self._is_connected = False

        self._client_lock.release()

    def is_connected(self):
        return self._client and self._is_connected

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._is_connected = True
            self.log.info('Connection to cloud.iO broker established')
            if self._on_connect_callback:
                self._on_connect_callback()
        else:
            if rc == 1:
                self.log.error('Connection refused - incorrect protocol version')
            elif rc == 2:
                self.log.error('Connection refused - invalid client identifier')
            elif rc == 3:
                self.log.error('Connection refused - server unavailable')
            elif rc == 4:
                self.log.error('Connection refused - bad username or password')
            elif rc == 5:
                self.log.error('Connection refused - not authorised')
            else:
                self.log.error('Connection refused - unknown reason')

    def on_disconnect(self, client, userdata, rc):
        self.log.info('Disconnect: %d' % rc)

        # Caution:
        # Do not call self.disconnect() here. It will kill the _thread calling this
        # method and any subsequent code will not be executed!
        # self.disconnect()

        # Notify container class if disconnect callback
        # was registered.
        if self._on_disconnect_callback:
            self._on_disconnect_callback(rc)
        else:
            self.log.warning('On disconnect callback not set')

    def on_message(self, client, userdata, msg):
        # Delegate to container class
        if self._on_message_callback:
            self._on_message_callback(client, userdata, msg)

    def on_published(self, client, userdata, mid):
        # print('Msg #{} sent'.format(mid))

        # Notify container class
        if self._on_message_published_callback:
            self._on_message_published_callback(client, userdata, mid)

    def publish(self, topic, payload=None, qos=0, retain=False):

        if not self.is_connected():
            message_info = mqtt.MQTTMessageInfo(mid=0)
            message_info.rc = mqtt.MQTT_ERR_INVAL
            return message_info

        message_info = self._client.publish(topic, payload, qos, retain)

        return message_info

    def subscribe(self, topic, qos=0):
        if self._client:
            return self._client.subscribe(topic, qos)
        else:
            return self.MQTT_ERR_NO_CONN, None


class MqttReconnectClient(MqttAsyncClient):
    """Same as MqttAsyncClient, but adds reconnect feature.
    """

    log = logging.getLogger('cloudio.mqttreconnectclient')

    def __init__(self, host, client_id='', clean_session=True, options=None):
        MqttAsyncClient.__init__(self, host, client_id, clean_session)

        # options are not used by MqttAsyncClient store them in this class
        self._options = options
        self._on_connected_callback = None
        self._on_connection_thread_finished_callback = None
        self._retry_interval = 10  # Connect retry interval in seconds
        self._auto_reconnect = True
        self._thread = None
        self._connect_timeout_event = Event()
        self._connection_thread_looping = True  # Set to false in case the connection _thread should leave

        # Register callback method to be called when connection to cloud.iO gets established
        MqttAsyncClient.set_on_connect_callback(self, self._on_connect)

        # Register callback method to be called when connection to cloud.iO gets lost
        MqttAsyncClient.set_on_disconnect_callback(self, self._on_disconnect)

    def set_on_connect_callback(self, on_connect):
        assert False, 'Not allowed in this class!'  # pragma: no cover

    def set_on_disconnect_callback(self, on_disconnect):
        assert False, 'Not allowed in this class!'  # pragma: no cover

    def set_on_connected_callback(self, on_connected_callback):
        self._on_connected_callback = on_connected_callback

    def set_on_connection_thread_finished_callback(self, on_connection_thread_finished_callback):
        self._on_connection_thread_finished_callback = on_connection_thread_finished_callback

    def start(self):
        self._start_connection_thread()

    def stop(self):
        self.log.info('Stopping MqttReconnectClient _thread')
        self._auto_reconnect = False
        self.disconnect()

    def _start_connection_thread(self):
        if self._thread is current_thread():
            # Do not restart myself!
            self.log.warning('Mqtt client connection _thread is me! Not restarting myself!')
            return
        if self._thread and self._thread.is_alive():
            self.log.warning('Mqtt client connection _thread already/still running!')
            return

        self._stop_connection_thread()

        self.log.info('Starting MqttReconnectClient _thread')
        self._thread = Thread(target=self._run, name='mqtt-reconnect-client-' + self._client_client_id)
        # Close _thread as soon as main _thread exits
        self._thread.setDaemon(True)

        self._connection_thread_looping = True
        self._thread.start()

    def _stop_connection_thread(self):
        self.log.info('Stopping MqttReconnectClient _thread')
        if self._thread:
            try:
                self._connection_thread_looping = False
                self._thread.join()
                self._thread = None
            except RuntimeError:
                self.log.error('Could not wait for connection _thread')
                traceback.print_exc()

    def _on_connect(self):
        self._connect_timeout_event.set()  # Free the connection _thread

    def _on_disconnect(self, rc):
        if self._auto_reconnect:
            self._start_connection_thread()

    def _on_connected(self):
        if self._on_connected_callback:
            self._on_connected_callback()

    def _on_connection_thread_finished(self):
        if self._on_connection_thread_finished_callback:
            self._on_connection_thread_finished_callback()

    ######################################################################
    # Active part
    #
    def _run(self):
        """Called by the internal _thread"""

        self.log.info('Mqtt client reconnect _thread running...')

        # Close any previous connection
        self.disconnect()

        while not self.is_connected() and self._connection_thread_looping:
            try:
                self._connect_timeout_event.clear()  # Reset connect timeout event prior to connect
                self.log.info('Trying to connect to cloud.iO...')
                self.connect(self._options)
            except Exception:
                traceback.print_exc()
                self.log.warning('Error during broker connect!')
                # Force disconnection of MQTT client
                self.disconnect(force_client_disconnect=False)
                # Do not exit here. Continue to try to connect

            # Check if _thread should leave
            if not self._connection_thread_looping:
                # Tell subscriber connection _thread has finished
                self._on_connection_thread_finished()
                return

            if not self.is_connected():
                # If we should not retry, give up
                if self._retry_interval > 0:
                    # Wait until it is time for the next connect
                    self._connect_timeout_event.wait(self._retry_interval)

                # If we should not retry, give up
                if self._retry_interval == 0:
                    break

        self.log.info('Thread: Job done - leaving')

        if self.is_connected():
            self.log.info('Connected to cloud.iO broker')

            # Tell subscriber we are connected
            self._on_connected()

        # Tell subscriber connection _thread has finished
        self._on_connection_thread_finished()


class MqttConnectOptions(object):
    def __init__(self):
        self.port = 8883  # Default port with ssl
        self.username = ''
        self.password = ''
        self.ca_file = None  # type: str or None
        self.client_cert_file = None  # type: str or None
        self.client_key_file = None  # type: str or None
        self.tls_version = None  # type: str or None
        self.will = None  # type dict
        self.jsonCert = None  # type: str or None

    def set_will(self, topic, message, qos, retained):
        self.will = {
            'topic': topic,
            'message': message,
            'qos': qos,
            'retained': retained
        }


class MqttClientPersistence(object):
    """Mimic the behavior of the java.MqttClientPersistence interface.

    Compatible with MQTT v3.

    See: https://www.eclipse.org/paho/files/javadoc/org/eclipse/paho/client/mqttv3/MqttClientPersistence.html
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    def clear(self):
        """Clears persistence, so that it no longer contains any persisted data.
        """
        raise NotImplementedError

    def close(self):
        """Close the persistent store that was previously opened.
        """
        raise NotImplementedError

    def contains_key(self, key):
        """Returns whether or not data is persisted using the specified key.

        :param key The key for data, which was used when originally saving it.
        :type key str
        :return True if key is present.
        """
        raise NotImplementedError

    def get(self, key):
        """Gets the specified data out of the persistent store.

        :param key The key for the data to be removed from the store.
        :type key str
        :return The wanted data.
        """
        raise NotImplementedError

    def keys(self):
        """Returns an Enumeration over the keys in this persistent data store.

        :return: generator
        """
        raise NotImplementedError

    def open(self, client_id, server_uri):
        """Initialise the persistent store.

        Initialise the persistent store. If a persistent store exists for this client ID then open it,
        otherwise create a new one. If the persistent store is already open then just return. An application
        may use the same client ID to connect to many different servers, so the client ID in conjunction
        with the connection will uniquely identify the persistence store required.

        :param client_id The client for which the persistent store should be opened.
        :type client_id str
        :param server_uri The connection string as specified when the MQTT client instance was created.
        :type server_uri str
        """
        raise NotImplementedError

    def put(self, key, persistable):
        """Puts the specified data into the persistent store.

        :param key The key for the data, which will be used later to retrieve it.
        :type key str
        :param persistable The data to persist.
        :type persistable bool
        """
        raise NotImplementedError

    def remove(self, key):
        """Remove the data for the specified key.

        :param key The key associated to the data to remove.
        :type key str
        :return None
        """
        raise NotImplementedError


class MqttMemoryPersistence(MqttClientPersistence):
    """Persistence store that uses memory.
    """

    def __init__(self):
        super(MqttMemoryPersistence, self).__init__()
        self._persistence = {}

    def open(self, client_id, server_uri):
        pass

    def close(self):
        self.clear()

    def put(self, key, persistable):
        self._persistence[key] = persistable

    def get(self, key):
        if key in self._persistence:
            return self._persistence[key]
        return None

    def contains_key(self, key):
        return True if key in self._persistence else False

    def keys(self):
        keys = []
        for key in self._persistence.keys():
            keys.append(key)
        return keys

    def remove(self, key):
        # Remove the key if it exist. If it does not exist
        # leave silently
        self._persistence.pop(key, None)

    def clear(self):
        self._persistence.clear()


class MqttDefaultFilePersistence(MqttClientPersistence):
    """Persistence store providing file based storage.
    """

    DEFAULT_DIRECTORY = '~/mqtt-persistence'

    def __init__(self, directory=None):
        """
        :param directory: Base directory where to store the persistent data
        """
        super(MqttDefaultFilePersistence, self).__init__()

        if directory is None or directory == '':
            directory = self.DEFAULT_DIRECTORY

        self._directory = path_helpers.prettify(directory)
        self._per_client_id_and_server_uri_directory = None  # type: str or None

        # Give a temporary unique storage name in case open() method does not get called
        self._per_client_id_and_server_uri_directory = str(uuid.uuid4())

        # Create base directory
        if not os.path.exists(self._directory):
            os.makedirs(self._directory)

    def open(self, client_id, server_uri):
        """Initialises the persistent store.

        :param client_id: MQTT client id
        :type client_id: str
        :param server_uri: Connection name to the server
        :type server_uri: str
        """
        self._per_client_id_and_server_uri_directory = client_id + '-' + server_uri

        # Remove some unwanted characters in sub-directory name
        self._per_client_id_and_server_uri_directory = self._per_client_id_and_server_uri_directory.replace('/', '')
        self._per_client_id_and_server_uri_directory = self._per_client_id_and_server_uri_directory.replace('\\', '')
        self._per_client_id_and_server_uri_directory = self._per_client_id_and_server_uri_directory.replace(':', '')
        self._per_client_id_and_server_uri_directory = self._per_client_id_and_server_uri_directory.replace(' ', '')

        # Create storage directory
        if not os.path.exists(self._storage_directory()):
            os.makedirs(self._storage_directory())

    def _storage_directory(self):
        return os.path.join(self._directory, self._per_client_id_and_server_uri_directory)

    def _key_file_name(self, key):
        return os.path.join(self._storage_directory(), key)

    def close(self):
        pass

    def put(self, key, persistable):
        """

        :param key:
        :param persistable:
        :type persistable: str or PendingUpdate
        :return:
        """

        # Convert string to PendingUpdate
        if isinstance(persistable, str):
            persistable = PendingUpdate(persistable)

        with open(self._key_file_name(key), mode='w') as file:
            # File is opened in binary mode. So bytes need to be stored
            # Convert str -> bytes
            file.write(persistable.get_data())

    def get(self, key):
        if os.path.exists(self._key_file_name(key)):
            with open(self._key_file_name(key), mode='r') as storage_file:
                return PendingUpdate(storage_file.read())
        return None

    def contains_key(self, key):
        return True if os.path.exists(self._key_file_name(key)) else False

    def keys(self):
        keys = next(os.walk(self._storage_directory()))[2]
        return keys

    def remove(self, key):
        # Remove the key if it exist. If it does not exist
        # leave silently
        key_file_name = self._key_file_name(key)
        try:
            if os.path.isfile(key_file_name):
                os.remove(key_file_name)
        except Exception:  # pragma: no cover
            pass  # pragma: no cover

    def clear(self):
        for key in os.listdir(self._storage_directory()):
            key_file_name = self._key_file_name(key)
            if os.path.isfile(key_file_name):
                os.remove(key_file_name)
