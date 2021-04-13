#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import os

import ssl

import time

from tests.cloudio.common.paths import update_working_directory
from cloudio.common import mqtt

update_working_directory()  # Needed when: 'pipenv run python -m unittest tests/cloudio/common/{this_file}.py'


class TestCloudioCommonMqttHelpers(unittest.TestCase):
    """Tests mqtt helpers module.
    """

    def test_mqtt_async_client_creation(self):
        client = mqtt.MqttAsyncClient(host=None)
        client._create_mqtt_client()

    def test_mqtt_async_client_callbacks(self):
        class CallbackProvider(object):
            def __init__(self):
                super(CallbackProvider, self).__init__()

            def set_on_connect_callback(self):
                pass

            def set_on_disconnect_callback(self):
                pass

            def set_on_message_callback(self):
                pass

            def set_on_message_published(self):
                pass

        clbk_provider = CallbackProvider()

        client = mqtt.MqttAsyncClient(host=None, client_id='test-id-')
        client.set_on_connect_callback(clbk_provider.set_on_connect_callback)
        client.set_on_disconnect_callback(clbk_provider.set_on_disconnect_callback)
        client.set_on_message_callback(clbk_provider.set_on_message_callback)
        client.set_on_message_published(clbk_provider.set_on_message_published)
        client._create_mqtt_client()

    def test_mqtt_async_client_connect_bad_options(self):
        import contextlib

        ca_file_name = 'ca-file.pem'
        client_cert_file_name = 'client-cert-file.pem'
        client_key_file_name = 'client-key-file.pem'

        # Delete local files
        with contextlib.suppress(FileNotFoundError):
            os.remove(ca_file_name)
            os.remove(client_cert_file_name)
            os.remove(client_key_file_name)

        client = mqtt.MqttAsyncClient(host=None)
        client._create_mqtt_client()

        with self.assertRaises(ValueError):  # ValueError: Invalid host
            options = mqtt.MqttConnectOptions()
            client.connect(options=options)
        client.disconnect()

        with self.assertRaises(RuntimeError):  # RuntimeError: CA file 'ca-file.pem' does not exist!
            options = mqtt.MqttConnectOptions()
            options.ca_file = ca_file_name
            client.connect(options=options)

        ca_file = open(ca_file_name, 'a')

        with self.assertRaises(RuntimeError):  # RuntimeError: Client certificate file 'client-cert-file.pem'
            # does not exist!
            options = mqtt.MqttConnectOptions()
            options.ca_file = ca_file_name
            options.client_cert_file = client_cert_file_name
            client.connect(options=options)

        client_cert_file = open(client_cert_file_name, 'a')

        with self.assertRaises(RuntimeError):  # RuntimeError: Client private key file 'client-key-file.pem'
            # does not exist!
            options = mqtt.MqttConnectOptions()
            options.ca_file = ca_file_name
            options.client_cert_file = client_cert_file_name
            options.client_key_file = client_key_file_name
            client.connect(options=options)

        client_key_file = open(client_key_file_name, 'a')

        with self.assertRaises(ssl.SSLError):  # ssl.SSLError: [SSL] PEM lib
            options = mqtt.MqttConnectOptions()
            options.ca_file = ca_file_name
            options.client_cert_file = client_cert_file_name
            options.client_key_file = client_key_file_name
            client.connect(options=options)

        # Tidy up
        ca_file.close()
        client_cert_file.close()
        client_key_file.close()
        with contextlib.suppress(FileNotFoundError):
            os.remove(ca_file_name)
            os.remove(client_cert_file_name)
            os.remove(client_key_file_name)

    def test_ssl_options_tls_versions(self):
        client = mqtt.MqttReconnectClient(host=None)
        options = mqtt.MqttConnectOptions()
        options.tls_version = 'tlsv1'

        with self.assertRaises(ValueError):  # ValueError: Invalid host.
            client.connect(options=options)

    def test_ssl_options_will(self):
        client = mqtt.MqttReconnectClient(host=None)
        options = mqtt.MqttConnectOptions()
        options.will = {'topic': '', }

        with self.assertRaises(KeyError):  # KeyError: 'message'
            client.connect(options=options)

        will_message = 'DEAD'
        options.set_will('@offline/VacuumCleanerEndpoint', will_message, 1, False)

        with self.assertRaises(ValueError):  # ValueError: Invalid host.
            client.connect(options=options)

    def test_option_password(self):

        client = mqtt.MqttReconnectClient(host=None)
        options = mqtt.MqttConnectOptions()
        options.username = 'test'
        options.password = 'tset'
        with self.assertRaises(ValueError):  # ValueError: Invalid host.
            client.connect(options=options)

    def test_mqtt_reconnect_client_creation(self):
        client = mqtt.MqttReconnectClient(host=None)
        self.assertFalse(client.is_connected())

    def test_mqtt_connection_using_vacuum_cleaner_endpoint(self):
        from cloudio.common.utils.resource_loader import ResourceLoader
        from cloudio.common.utils.resource_loader import prettify

        endpoint_config = 'VacuumCleanerEndpoint.properties'
        config = ResourceLoader.load_from_locations(endpoint_config, ['home:/.config/cloud.io', ])
        self.assertNotEqual(config, dict())

        options = mqtt.MqttConnectOptions()
        options.ca_file = prettify(config['ch.hevs.cloudio.endpoint.ssl.authorityCert'])
        options.client_cert_file = prettify(config['ch.hevs.cloudio.endpoint.ssl.clientCert'])
        options.client_key_file = prettify(config['ch.hevs.cloudio.endpoint.ssl.clientKey'])

        client = mqtt.MqttReconnectClient(host=config['ch.hevs.cloudio.endpoint.hostUri'],
                                          client_id='test-vacuum-cleaner' + '-endpoint-',
                                          clean_session=True,
                                          options=options)

        client.start()
        time.sleep(2)
        client.stop()

    def test_mqtt_publish_receive_message(self):
        from cloudio.common.utils.resource_loader import ResourceLoader
        from cloudio.common.utils.resource_loader import prettify

        class VacuumCleanerModel(object):
            def __init__(self, mqtt_client: mqtt.MqttReconnectClient):
                super(VacuumCleanerModel, self).__init__()
                self._client = mqtt_client

                mqtt_client.set_on_connected_callback(self.on_connected_callback)
                mqtt_client.set_on_connection_thread_finished_callback(self.on_connection_thread_finished_callback)
                mqtt_client.set_on_message_callback(self.on_message_callback)
                mqtt_client.set_on_message_published(self.on_message_published)

                self.connected = False
                self.conn_thread_finished = False
                self.msg_received = False
                self.received_topic = ''
                self.msg_published = False

            def on_connected_callback(self):
                self.connected = True

                # Subscribe to '@set' message
                self._client.subscribe('@set/' + 'VacuumCleanerEndpoint' + '/#', 1)

                # Test subscription by sending a '@set' message
                self._client.publish('@set/VacuumCleanerEndpoint/test', '{"value":"1" }')

            def on_connection_thread_finished_callback(self):
                self.conn_thread_finished = True

            def on_message_callback(self, client, userdata, msg):
                self.msg_received = True
                self.received_topic = msg.topic

            def on_message_published(self, client, userdata, mid):
                self.msg_published = True

        endpoint_config = 'VacuumCleanerEndpoint.properties'
        config = ResourceLoader.load_from_locations(endpoint_config, ['home:/.config/cloud.io', ])
        self.assertNotEqual(config, dict())

        options = mqtt.MqttConnectOptions()
        options.ca_file = prettify(config['ch.hevs.cloudio.endpoint.ssl.authorityCert'])
        options.client_cert_file = prettify(config['ch.hevs.cloudio.endpoint.ssl.clientCert'])
        options.client_key_file = prettify(config['ch.hevs.cloudio.endpoint.ssl.clientKey'])

        client = mqtt.MqttReconnectClient(host=config['ch.hevs.cloudio.endpoint.hostUri'],
                                          client_id='test-vacuum-cleaner' + '-endpoint-',
                                          clean_session=True,
                                          options=options)

        model = VacuumCleanerModel(client)

        client.start()
        time.sleep(2)
        client.stop()

        self.assertTrue(model.connected)
        self.assertTrue(model.conn_thread_finished)
        self.assertTrue(model.msg_received)
        self.assertTrue('test' in model.received_topic)
        self.assertTrue(model.msg_published)


class TestCloudioCommonMqttDataStorage(unittest.TestCase):
    """Tests persistence classes in mqtt helpers module.
    """

    def test_mqtt_file_persistence(self):
        from cloudio.common.utils import path_helpers
        from shutil import rmtree

        test_directory = path_helpers.path_from_file(__file__)
        data_storage = mqtt.MqttDefaultFilePersistence(directory=test_directory)

        # remove directory
        rmtree(os.path.join(test_directory, 'test-test'), ignore_errors=True)

        data_storage.open('test', 'test')

        data_storage.put(key='food', persistable='salad')

        data = data_storage.get('food')
        self.assertEqual(data.get_data(), 'salad')

        data = data_storage.get('bolds')
        self.assertIsNone(data)

        key = data.get_uuid_from_persistence_key('-test-it-with-uuid-name-whatever')
        self.assertEqual(key, 'uuid-name')

        data_storage.close()

    def test_mqtt_file_persistence_access(self):
        from cloudio.common.utils import path_helpers
        test_directory = path_helpers.path_from_file(__file__)
        data_storage = mqtt.MqttDefaultFilePersistence(directory=test_directory)

        data_storage.open('test', 'test')

        data_storage.put(key='food', persistable='salad')
        data_storage.put(key='drink', persistable='water')

        keys = data_storage.keys()
        self.assertListEqual(keys, ['drink', 'food'])

        self.assertTrue(data_storage.contains_key('food'))
        self.assertTrue(data_storage.contains_key('drink'))
        self.assertFalse(data_storage.contains_key('nuts'))

        data_storage.remove('drink')
        self.assertListEqual(data_storage.keys(), ['food'])

        data_storage.remove('stone')

        data_storage.clear()

        keys = data_storage.keys()
        self.assertListEqual(keys, [])

        data_storage.close()
