#!/usr/bin/env python

"""
Backend to support Brother QL-series printers via network.
Works cross-platform.
"""

import socket, os, time, select

from .generic import BrotherQLBackendGeneric

def list_available_devices():
    """
    List all available devices for the network backend

    returns: devices: a list of dictionaries with the keys 'string_descr' and 'instance': \
        [ {'string_descr': 'tcp://hostname[:port]', 'instance': None}, ] \
        Instance is set to None because we don't want to connect to the device here yet.
    """

    # We need some snmp request sent to 255.255.255.255 here
    raise NotImplementedError()
    return [{'string_descr': 'tcp://' + path, 'instance': None} for path in paths]

class BrotherQLBackendNetwork(BrotherQLBackendGeneric):
    """
    BrotherQL backend using the Linux Kernel USB Printer Device Handles
    """

    def __init__(self, device_specifier):
        """
        device_specifier: string or os.open(): string descriptor in the \
            format file:///dev/usb/lp0 or os.open() raw device handle.
        """

        self.read_timeout = 0.01
        # strategy : try_twice, select or socket_timeout
        self.strategy = 'socket_timeout'
        if isinstance(device_specifier, str):
            if device_specifier.startswith('tcp://'):
                device_specifier = device_specifier[6:]
            host, _, port = device_specifier.partition(':')
            if port:
                port = int(port)
            else:
                port = 9100
            #try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.s.connect((host, port))
            #except OSError as e:
            #    raise ValueError('Could not connect to the device.')
            if self.strategy == 'socket_timeout':
                self.s.settimeout(self.read_timeout)
            elif self.strategy == 'try_twice':
                self.s.settimeout(self.read_timeout)
            else:
                self.s.settimeout(0)

        elif isinstance(device_specifier, int):
            self.dev = device_specifier
        else:
            raise NotImplementedError('Currently the printer can be specified either via an appropriate string or via an os.open() handle.')

    def _write(self, data):
        self.s.send(data)

    def _read(self, length=32):
        if self.strategy in ('socket_timeout', 'try_twice'):
            if self.strategy == 'socket_timeout':
                tries = 1
            if self.strategy == 'try_twice':
                tries = 2
            for i in range(tries):
                try:
                    data = self.s.recv(length)
                    return data
                except socket.timeout:
                    pass
            return b''
        elif self.strategy == 'select':
            data = b''
            start = time.time()
            while (not data) and (time.time() - start < self.read_timeout):
                result, _, _ = select.select([self.s], [], [], 0)
                if self.s in result:
                    data += self.s.recv(length)
                if data: break
                time.sleep(0.001)
            return data
        else:
            raise NotImplementedError('Unknown strategy')

    def _dispose(self):
        self.s.shutdown(socket.SHUT_RDWR)
        self.s.close()
