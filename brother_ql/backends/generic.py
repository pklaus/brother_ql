
import logging

logger = logging.getLogger(__name__)

def list_available_devices():
    """ List all available devices for the respective backend """
    # returns a list of dictionaries with the keys 'string_descr' and 'instance':
    # [ {'string_descr': '/dev/usb/lp0', 'instance': os.open('/dev/usb/lp0', os.O_RDWR)}, ]
    raise NotImplementedError()


class BrotherQLBackendGeneric(object):

    def __init__(self, device_specifier):
        """
        device_specifier can be either a string or an instance
        of the required class type.
        """
        self.write_dev = None
        self.read_dev  = None
        raise NotImplementedError()

    def _write(self, data):
        self.write_dev.write(data)

    def _read(self, length=32):
        return bytes(self.read_dev.read(length))

    def write(self, data):
        logger.debug('Writing %d bytes.', len(data))
        self._write(data)

    def read(self, length=32):
        try:
            ret_bytes = self._read(length)
            if ret_bytes: logger.debug('Read %d bytes.', len(ret_bytes))
            return ret_bytes
        except Exception as e:
            logger.debug('Error reading... %s', e)
            raise

    def dispose(self):
        try:
            self._dispose()
        except:
            pass

    def _dispose(self):
        raise NotImplementedError()

    def __del__(self):
        self.dispose()
