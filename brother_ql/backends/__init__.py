
from .generic import BrotherQLBackendGeneric


available_backends = [
  'pyusb',
  'network',
  'linux_kernel',
]

def guess_backend(descr):
    """ guess the backend from a given string descriptor for the device """
    if descr.startswith('usb://') or descr.startswith('0x'):
        return 'pyusb'
    elif descr.startswith('file://') or descr.startswith('/dev/usb/') or descr.startswith('lp'):
        return 'linux_kernel'
    elif descr.startswith('tcp://'):
        return 'network'
    else:
        raise ValueError('Cannot guess backend for given string descriptor: %s' % descr)
    

def backend_factory(backend_name):

    if backend_name == 'pyusb':
        from . import pyusb        as pyusb_backend
        list_available_devices = pyusb_backend.list_available_devices
        backend_class          = pyusb_backend.BrotherQLBackendPyUSB
    elif backend_name == 'linux_kernel':
        from . import linux_kernel as linux_kernel_backend
        list_available_devices = linux_kernel_backend.list_available_devices
        backend_class          = linux_kernel_backend.BrotherQLBackendLinuxKernel
    elif backend_name == 'network':
        from . import network      as network_backend
        list_available_devices = network_backend.list_available_devices
        backend_class          = network_backend.BrotherQLBackendNetwork
    else:
        raise NotImplementedError('Backend %s not implemented.' % backend_name)

    return {'list_available_devices': list_available_devices, 'backend_class': backend_class}
