#!/usr/bin/env python

"""
Backend to support Brother QL-series printers via PyUSB.
Works on Mac OS X and Linux.

Requires PyUSB: https://github.com/walac/pyusb/
Install via `pip install pyusb`
"""

import time

import usb.core
import usb.util

from .generic import BrotherQLBackendGeneric

def list_available_devices():
    """
    List all available devices for the respective backend

    returns: devices: a list of dictionaries with the keys 'string_descr' and 'instance': \
        [ {'string_descr': 'usb://0x04f9:0x2015/C5Z315686', 'instance': pyusb.core.Device()}, ]
        The 'string_descr' is of the format idVendor:idProduct_iSerialNumber.
    """

    class find_class(object):
        def __init__(self, class_):
            self._class = class_
        def __call__(self, device):
            # first, let's check the device
            if device.bDeviceClass == self._class:
                return True
            # ok, transverse all devices to find an interface that matches our class
            for cfg in device:
                # find_descriptor: what's it?
                intf = usb.util.find_descriptor(cfg, bInterfaceClass=self._class)
                if intf is not None:
                    return True
            return False

    # only Brother printers
    printers = usb.core.find(find_all=1, custom_match=find_class(7), idVendor=0x04f9)

    def string_descr(dev):
        try:
            serial = usb.util.get_string(dev, 256, dev.iSerialNumber)
            return 'usb://0x{:04x}:0x{:04x}_{}'.format(dev.idVendor, dev.idProduct, serial)
        except:
            return 'usb://0x{:04x}:0x{:04x}'.format(dev.idVendor, dev.idProduct)

    return [{'string_descr': string_descr(printer), 'instance': printer} for printer in printers]

class BrotherQLBackendPyUSB(BrotherQLBackendGeneric):
    """
    BrotherQL backend using PyUSB
    """

    def __init__(self, device_specifier):
        """
        device_specifier: string or pyusb.core.Device: string descriptor of the \
            format usb://brother_ql/idVendor/idProduct/iSerialNumber or pyusb.core.Device instance.
        """

        self.dev = None
        self.read_timeout =    10. # ms
        self.write_timeout = 5000. # ms
        # strategy : try_twice or select
        self.strategy = 'try_twice'
        if isinstance(device_specifier, str):
            if device_specifier.startswith('usb://'):
                device_specifier = device_specifier[6:]
            vendor_product, _, serial = device_specifier.partition('/')
            vendor, _, product = vendor_product.partition(':')
            vendor, product = int(vendor, 16), int(product, 16)
            for result in list_available_devices():
                printer = result['instance']
                if printer.idVendor == vendor and printer.idProduct == product or (serial and printer.iSerialNumber == serial):
                    self.dev = printer
                    break
            if self.dev is None:
                raise ValueError('Device not found')
        elif isinstance(device_specifier, usb.core.Device):
            self.dev = device_specifier
        else:
            raise NotImplementedError('Currently the printer can be specified either via an appropriate string or via a usb.core.Device instance.')

        # Now we are sure to have self.dev around, start using it:

        try:
            assert self.dev.is_kernel_driver_active(0)
            self.dev.detach_kernel_driver(0)
            self.was_kernel_driver_active = True
        except (NotImplementedError, AssertionError):
            self.was_kernel_driver_active = False

        # set the active configuration. With no arguments, the first configuration will be the active one
        self.dev.set_configuration()

        cfg = self.dev.get_active_configuration()
        intf = cfg[(0,0)]

        ep_match_in  = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
        ep_match_out = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT

        ep_in  = usb.util.find_descriptor(intf, custom_match=ep_match_in)
        ep_out = usb.util.find_descriptor(intf, custom_match=ep_match_out)

        assert ep_in  is not None
        assert ep_out is not None

        self.write_dev = ep_out
        self.read_dev  = ep_in

    def _raw_read(self, length):
        # pyusb Device.read() operations return array() type - let's convert it to bytes()
        return bytes(self.read_dev.read(length))

    def _read(self, length=32):
        if self.strategy == 'try_twice':
            data = self._raw_read(length)
            if data:
                return bytes(data)
            else:
                time.sleep(self.read_timeout/1000.)
                return self._raw_read(length)
        elif self.strategy == 'select':
            data = b''
            start = time.time()
            while (not data) and (time.time() - start < self.read_timeout/1000.):
                result, _, _ = select.select([self.read_dev], [], [], 0)
                if self.read_dev in result:
                    data += self._raw_read(length)
                if data: break
                time.sleep(0.001)
            if not data:
                # one last try if still no data:
                return self._raw_read(length)
            else:
                return data
        else:
            raise NotImplementedError('Unknown strategy')

    def _write(self, data):
        self.write_dev.write(data, int(self.write_timeout))

    def _dispose(self):
        usb.util.dispose_resources(self.dev)
        del self.write_dev, self.read_dev
        if self.was_kernel_driver_active:
            self.dev.attach_kernel_driver(0)
        del self.dev
