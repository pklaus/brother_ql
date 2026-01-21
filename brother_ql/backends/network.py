#!/usr/bin/env python

"""
Backend to support Brother QL-series printers via network.
Works cross-platform.
"""

from __future__ import unicode_literals
from builtins import str
import enum

from pysnmp.proto.rfc1157 import VarBind
from pysnmp.proto import api
from pysnmp import hlapi

import socket
from time import time

from enum import Enum

from . import quicksnmp
from .generic import BrotherQLBackendGeneric

# Some SNMP OID's that we can use to get printer information
class Brother_SNMP_OID(Enum):
    '''SNMP OID's'''
    GET_IP       = "1.3.6.1.4.1.1240.2.3.4.5.2.3.0"
    GET_NETMASK  = "1.3.6.1.4.1.1240.2.3.4.5.2.4.0"
    GET_MAC      = "1.3.6.1.4.1.1240.2.3.4.5.2.4.0"
    GET_LOCATION = "1.3.6.1.2.1.1.6.0"
    GET_MODEL    = "1.3.6.1.2.1.25.3.2.1.3.1"
    GET_SERIAL   = "1.3.6.1.2.1.43.5.1.1.17"
    GET_STATUS   = "1.3.6.1.4.1.2435.3.3.9.1.6.1.0"

# SNMP Contants 
SNMP_MAX_WAIT_FOR_RESPONSES = 5
SNMP_MAX_NUMBER_OF_RESPONSES = 10

# Global variables
Broadcast_Started_At = 0
foundPrinters = set()

def list_available_devices():
    """
    List all available devices for the network backend

    returns: devices: a list of dictionaries with the keys 'identifier' and 'instance': \
        [ {'identifier': 'tcp://hostname[:port]', 'instance': None}, ] \
        Instance is set to None because we don't want to connect to the device here yet.
    """
    # Protocol version to use
    pMod = api.protoModules[api.protoVersion1]

    # Build PDU
    reqPDU = pMod.GetRequestPDU()
    pMod.apiPDU.setDefaults(reqPDU)
    pMod.apiPDU.setVarBinds(
        reqPDU, [(Brother_SNMP_OID.GET_IP.value, pMod.Null(''))]
    )

    # Build message
    reqMsg = pMod.Message()
    pMod.apiMessage.setDefaults(reqMsg)
    pMod.apiMessage.setCommunity(reqMsg, 'public')
    pMod.apiMessage.setPDU(reqMsg, reqPDU)

    # Clear current list of found printers
    foundPrinters.clear()

    # set start time for timeout timer
    Broadcast_Started_At = time()

    # We need some snmp request sent to 255.255.255.255 here
    try:
        quicksnmp.broadcastSNMPReq(reqMsg, cbRecvFun, cbTimerFun, SNMP_MAX_NUMBER_OF_RESPONSES)
    except TimeoutTimerExpired:
        pass

    #raise NotImplementedError()
    return [{'identifier': 'tcp://' + printer, 'instance': None} for printer in foundPrinters]

class BrotherQLBackendNetwork(BrotherQLBackendGeneric):
    """
    BrotherQL backend using the Linux Kernel USB Printer Device Handles
    """

    def __init__(self, device_specifier):
        """
        device_specifier: string or os.open(): identifier in the \
            format tcp://<ipaddress>:<port> or os.open() raw device handle.
        """

        self.read_timeout = 0.01
        # strategy : try_twice, select or socket_timeout
        self.strategy = 'socket_timeout'
        if isinstance(device_specifier, str):
            if device_specifier.startswith('tcp://'):
                device_specifier = device_specifier[6:]
            self.host, _, port = device_specifier.partition(':')
            if port:
                port = int(port)
            else:
                port = 9100
            try:
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.s.connect((self.host, port))
            except socket.error as e:
                raise ValueError('Could not connect to the device.') from e
            if self.strategy in ('socket_timeout', 'try_twice'):
                self.s.settimeout(self.read_timeout)
            else:
                self.s.settimeout(0)
        else:
            raise NotImplementedError('Currently the printer can be \
                specified either via an appropriate string.')

    def _write(self, data):
        self.s.settimeout(10)
        self.s.sendall(data)
        self.s.settimeout(self.read_timeout)

    def _read(self, length=32):
        if self.strategy in ('socket_timeout', 'try_twice'):
            if self.strategy == 'socket_timeout':
                tries = 1
            if self.strategy == 'try_twice':
                tries = 2
            for i in range(tries):
                try:
                    # Using SNMP, we retrieve the status of the remote device
                    dataset = quicksnmp.get(self.host,
                                            [Brother_SNMP_OID.GET_STATUS.value],
                                            hlapi.CommunityData('public'))
                    return dataset[Brother_SNMP_OID.GET_STATUS.value]
                except socket.timeout:
                    pass
            return b''
        else:
            raise NotImplementedError('Unknown strategy')

    def _dispose(self):
        self.s.shutdown(socket.SHUT_RDWR)
        self.s.close()

class TimeoutTimerExpired(Exception):
    '''Timeout timer expired exception'''

def cbTimerFun(timeNow):
    '''Countdown callback to check if the requested wait time has elapased'''
    if timeNow - Broadcast_Started_At > SNMP_MAX_WAIT_FOR_RESPONSES:
        raise TimeoutTimerExpired


def cbRecvFun(transportDispatcher, transportDomain, 
                transportAddress, wholeMsg):
    '''Receive SNMP data callback'''
    foundPrinters.add(f"{transportAddress[0]}")
    return wholeMsg
