#!/usr/bin/env python

"""
Backend to support Brother QL-series printers via Windows Print Spooler.
Works on Windows only.

Uses the native Windows printer driver through ctypes/winspool API.
No external dependencies required - uses only stdlib ctypes.
"""

from __future__ import unicode_literals
from builtins import str, bytes

import logging
import ctypes
from ctypes import wintypes

from .generic import BrotherQLBackendGeneric

logger = logging.getLogger(__name__)

def list_available_devices():
    """
    List all available Windows printers that might be Brother QL printers.
    
    returns: devices: a list of dictionaries with the keys 'identifier' and 'instance': \
        [ {'identifier': 'windows://Brother QL-500', 'instance': None}, ]
    """
    try:
        import winreg
        devices = []
        
        # Look in Windows registry for Brother printers
        try:
            reg_path = r"SYSTEM\CurrentControlSet\Control\Print\Printers"
            registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
            
            i = 0
            while True:
                try:
                    printer_name = winreg.EnumKey(registry_key, i)
                    if 'Brother' in printer_name or 'QL' in printer_name:
                        devices.append({
                            'identifier': f'windows://{printer_name}',
                            'instance': None
                        })
                    i += 1
                except WindowsError:
                    break
            
            winreg.CloseKey(registry_key)
        except Exception as e:
            logger.debug(f"Could not enumerate printers from registry: {e}")
        
        # Fallback: return common Brother QL printer names
        if not devices:
            common_names = ['Brother QL-500', 'Brother QL-550', 'Brother QL-600', 'Brother QL-700']
            devices = [{'identifier': f'windows://{name}', 'instance': None} for name in common_names]
        
        return devices
    except Exception as e:
        logger.error(f"Error listing Windows printers: {e}")
        return []


class BrotherQLBackendWindows(BrotherQLBackendGeneric):
    """
    BrotherQL backend using Windows Print Spooler
    """

    def __init__(self, device_specifier):
        """
        device_specifier: string identifier in the format windows://PrinterName
        
        Example: windows://Brother QL-500
        """
        
        self.printer_name = None
        self.hprinter = None
        
        if isinstance(device_specifier, str):
            if device_specifier.startswith('windows://'):
                self.printer_name = device_specifier[10:]  # Remove 'windows://' prefix
            else:
                self.printer_name = device_specifier
        else:
            raise NotImplementedError('device_specifier must be a string like "windows://Brother QL-500"')
        
        if not self.printer_name:
            raise ValueError('Invalid printer name')
        
        logger.info(f'Initializing Windows printer backend for: {self.printer_name}')
        
        # Verify printer exists by trying to open it
        try:
            self._open_printer()
            self._close_printer()
        except Exception as e:
            raise ValueError(f'Could not open printer "{self.printer_name}": {e}')
    
    def _open_printer(self):
        """Open a handle to the printer"""
        if self.hprinter is not None:
            return
        
        # Load winspool.drv explicitly
        winspool = ctypes.WinDLL('winspool.drv')
        
        self.hprinter = wintypes.HANDLE()
        result = winspool.OpenPrinterW(
            ctypes.c_wchar_p(self.printer_name),
            ctypes.byref(self.hprinter),
            None
        )
        
        if not result:
            raise OSError(f'Failed to open printer: {self.printer_name}')
    
    def _close_printer(self):
        """Close the printer handle"""
        if self.hprinter is not None:
            winspool = ctypes.WinDLL('winspool.drv')
            winspool.ClosePrinter(self.hprinter)
            self.hprinter = None
    
    def _write(self, data):
        """Write data to the printer"""
        try:
            self._open_printer()
            
            # Load winspool.drv
            winspool = ctypes.WinDLL('winspool.drv')
            
            # WritePrinter requires the data as bytes
            if isinstance(data, str):
                data = data.encode('latin-1')
            
            # Define DOC_INFO_1 structure for StartDocPrinter
            class DOC_INFO_1(ctypes.Structure):
                _fields_ = [
                    ("pDocName", wintypes.LPWSTR),
                    ("pOutputFile", wintypes.LPWSTR),
                    ("pDatatype", wintypes.LPWSTR),
                ]
            
            # Start a print job
            doc_info = DOC_INFO_1()
            doc_info.pDocName = "Brother QL Label"
            doc_info.pOutputFile = None
            doc_info.pDatatype = "RAW"  # RAW mode - send data directly to printer
            
            job_id = winspool.StartDocPrinterW(self.hprinter, 1, ctypes.byref(doc_info))
            if not job_id:
                raise IOError('StartDocPrinter failed')
            
            try:
                # Start a page
                if not winspool.StartPagePrinter(self.hprinter):
                    raise IOError('StartPagePrinter failed')
                
                # Write the data
                written = wintypes.DWORD()
                result = winspool.WritePrinter(
                    self.hprinter,
                    data,
                    len(data),
                    ctypes.byref(written)
                )
                
                if not result:
                    raise IOError(f'WritePrinter failed. Bytes written: {written.value} of {len(data)}')
                
                logger.debug(f'Wrote {written.value} bytes to printer')
                
                # End the page
                if not winspool.EndPagePrinter(self.hprinter):
                    logger.warning('EndPagePrinter failed')
                
            finally:
                # End the document (print job)
                if not winspool.EndDocPrinter(self.hprinter):
                    logger.warning('EndDocPrinter failed')
            
        except Exception as e:
            logger.error(f'Error writing to printer: {e}')
            raise
    
    def _read(self, length=32):
        """
        Windows Print Spooler does not support reading back from the printer.
        Always returns empty bytes.
        """
        return bytes()
    
    def dispose(self):
        """Clean up resources"""
        try:
            self._close_printer()
        except:
            pass
    
    def __del__(self):
        """Destructor to ensure printer is closed"""
        self.dispose()
