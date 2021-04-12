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

            def set_on_messsage_published(self):
                pass

        clbk_provider = CallbackProvider()

        client = mqtt.MqttAsyncClient(host=None, client_id='test-id-')
        client.set_on_connect_callback(clbk_provider.set_on_connect_callback)
        client.set_on_disconnect_callback(clbk_provider.set_on_disconnect_callback)
        client.set_on_message_callback(clbk_provider.set_on_message_callback)
        client.set_on_messsage_published(clbk_provider.set_on_messsage_published)
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

        with self.assertRaises(ValueError): # ValueError: Invalid host.
            client.connect(options=options)

    def test_ssl_options_will(self):
        client = mqtt.MqttReconnectClient(host=None)
        options = mqtt.MqttConnectOptions()
        options.will = {'topic': '', }

        with self.assertRaises(KeyError):  # KeyError: 'message'
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

