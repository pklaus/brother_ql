from pysnmp import hlapi
from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
from pysnmp.carrier.asyncore.dgram import udp
from pyasn1.codec.ber import encoder, decoder
from pysnmp.proto import api
from time import time
from pyasn1.type.univ import OctetString

def construct_object_types(list_of_oids):
    object_types = []
    for oid in list_of_oids:
        object_types.append(hlapi.ObjectType(hlapi.ObjectIdentity(oid)))
    return object_types


def construct_value_pairs(list_of_pairs):
    pairs = []
    for key, value in list_of_pairs.items():
        pairs.append(hlapi.ObjectType(hlapi.ObjectIdentity(key), value))
    return pairs


def set(target, value_pairs, credentials, port=161, engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    handler = hlapi.setCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        *construct_value_pairs(value_pairs)
    )
    return fetch(handler, 1)[0]


def get(target, oids, credentials, port=161, engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    handler = hlapi.getCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        *construct_object_types(oids)
    )
    return fetch(handler, 1)[0]


def get_bulk(target, oids, credentials, count, start_from=0, port=161,
             engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    handler = hlapi.bulkCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        start_from, count,
        *construct_object_types(oids)
    )
    return fetch(handler, count)


def get_bulk_auto(target, oids, credentials, count_oid, start_from=0, port=161,
                  engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    count = get(target, [count_oid], credentials, port, engine, context)[count_oid]
    return get_bulk(target, oids, credentials, count, start_from, port, engine, context)


def cast(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        try:
            return float(value)
        except (ValueError, TypeError):
            try:
                return str(value, 'UTF-8')
            except (ValueError, TypeError):
                pass
    return value


def fetch(handler, count):
    result = []
    for i in range(count):
        try:
            error_indication, error_status, error_index, var_binds = next(handler)
            if not error_indication and not error_status:
                items = {}
                for var_bind in var_binds:
                    items[str(var_bind[0])] = cast(var_bind[1])
                result.append(items)
            else:
                raise RuntimeError('Got SNMP error: {0}'.format(error_indication))
        except StopIteration:
            break
    return result


def broadcastSNMPReq(reqMsg, cbRecvFun, cbTimerFun, max_number_of_responses=10):
    '''TODO'''
    transportDispatcher = AsyncoreDispatcher()
    transportDispatcher.registerRecvCbFun(cbRecvFun)
    transportDispatcher.registerTimerCbFun(cbTimerFun)

    # UDP/IPv4
    udpSocketTransport = udp.UdpSocketTransport().openClientMode().enableBroadcast()
    transportDispatcher.registerTransport(udp.domainName, udpSocketTransport)

    # Pass message to dispatcher
    transportDispatcher.sendMessage(
        encoder.encode(reqMsg), udp.domainName, ('255.255.255.255', 161)
    )

    # wait for a maximum of responses or time out
    transportDispatcher.jobStarted(1, max_number_of_responses)

    # Dispatcher will finish as all jobs counter reaches zero
    try:
        transportDispatcher.runDispatcher()
    finally:
        transportDispatcher.closeDispatcher()
