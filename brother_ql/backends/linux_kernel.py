#!/usr/bin/env python

"""
Backend to support Brother QL-series printers via the linux kernel USB printer interface.
Works on Linux.
"""

import glob, os, time, select

from .generic import BrotherQLBackendGeneric

def list_available_devices():
    """
    List all available devices for the linux kernel backend

    returns: devices: a list of dictionaries with the keys 'string_descr' and 'instance': \
        [ {'string_descr': 'file:///dev/usb/lp0', 'instance': None}, ] \
        Instance is set to None because we don't want to open (and thus potentially block) the device here.
    """

    paths = glob.glob('/dev/usb/lp*')

    return [{'string_descr': 'file://' + path, 'instance': None} for path in paths]

class BrotherQLBackendLinuxKernel(BrotherQLBackendGeneric):
    """
    BrotherQL backend using the Linux Kernel USB Printer Device Handles
    """

    def __init__(self, device_specifier):
        """
        device_specifier: string or os.open(): string descriptor in the \
            format file:///dev/usb/lp0 or os.open() raw device handle.
        """

        self.read_timeout = 0.01
        # strategy : try_twice or select
        self.strategy = 'select'
        if isinstance(device_specifier, str):
            if device_specifier.startswith('file://'):
                device_specifier = device_specifier[7:]
            self.dev = os.open(device_specifier, os.O_RDWR)
        elif isinstance(device_specifier, int):
            self.dev = device_specifier
        else:
            raise NotImplementedError('Currently the printer can be specified either via an appropriate string or via an os.open() handle.')

        self.write_dev = self.dev
        self.read_dev  = self.dev

    def _write(self, data):
        os.write(self.write_dev, data)

    def _read(self, length=32):
        if self.strategy == 'try_twice':
            data = os.read(self.read_dev, length)
            if data:
                return data
            else:
                time.sleep(self.read_timeout)
                return os.read(self.read_dev, length)
        elif self.strategy == 'select':
            data = b''
            start = time.time()
            while (not data) and (time.time() - start < self.read_timeout):
                result, _, _ = select.select([self.read_dev], [], [], 0)
                if self.read_dev in result:
                    data += os.read(self.read_dev, length)
                if data: break
                time.sleep(0.001)
            if not data:
                # one last try if still no data:
                return os.read(self.read_dev, length)
            else:
                return data
        else:
            raise NotImplementedError('Unknown strategy')

    def _dispose(self):
        os.close(self.dev)
