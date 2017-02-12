import hidapi as hid

class MSIKeyboard:
    vendorID = 0x1770
    productID = 0xFF00
    serial = "MSI EPF USB"
    
    REPORT_ID = b'\x01'
    PREAMBLE = b'\x02'
    LAST_BYTE = b'\x00'
    
    CMD_SET_MODE = b'\x41'
    CMD_SET_ZONE_COLOR_NORMAL = b'\x40'
    CMD_SET_DUAL_MODE_ATTRIBUTE = b'\x44'
    
    KB_MODE_OFF = b'\x00'
    KB_MODE_NORMAL = b'\x01'
    KB_MODE_GAMING = b'\x02'
    KB_MODE_BREATHE = b'\x03'
    KB_MODE_DEMO = b'\x04'
    KB_MODE_WAVE = b'\x05'
    KB_MODE_DUAL = b'\x06'
    KB_MODE_DEFAULT = b'\x0A'
    
    plain_modes = {
        'red': 16, 
        'orange': 17, 
        'yellow': 18, 
        'green': 19, 
        'sky': 20, 
        'blue': 21, 
        'violet': 22, 
        'white': 23, 
        'faint-white': 24, 
        'faint-red': 26, 
        'faint-green': 27, 
        'faint-blue': 28
    }
    
    def __init__(self):
        self.dev = hid.Device(vendor_id=self.vendorID, product_id=self.productID, serial_number=self.serial)
        self.state = 'stop'
        
    def _sendCommand(self, command, arg1=b'\x00', arg2=b'\x00', arg3=b'\x00', arg4=b'\x00'):
        report = self.PREAMBLE + command + arg1 + arg2 + arg3 + arg4 + self.LAST_BYTE
        self.dev.send_feature_report(report, self.REPORT_ID)
        
    def _setMode(self, mode):
        self._sendCommand(self.CMD_SET_MODE, mode)
        
    def _setZoneColorNormal(self, zone, r, g, b):
        self._sendCommand(self.CMD_SET_ZONE_COLOR_NORMAL, zone.to_bytes(1, 'little'), r.to_bytes(1, 'little'), g.to_bytes(1, 'little'), b.to_bytes(1, 'little'))
        
    def _setDualModeAttribute(self, attribute, arg1=0, arg2=0, arg3=0):
        self._sendCommand(self.CMD_SET_DUAL_MODE_ATTRIBUTE, attribute.to_bytes(1, 'little'), arg1.to_bytes(1, 'little'), arg2.to_bytes(1, 'little'), arg3.to_bytes(1, 'little'))
    
    def _setDualModeZone(self, zone, color_a=(255, 255, 255), color_b=(255, 255, 255), color_fade_time=(0, 0, 0)):
        zidx = (zone-1) * 3 + 1
        self._setDualModeAttribute(zidx + 0, *color_a)
        self._setDualModeAttribute(zidx + 1, *color_b)
        self._setDualModeAttribute(zidx + 2, *color_fade_time)
        self._setMode(self.KB_MODE_DUAL)
    
    def SetOffMode(self):
        self._setMode(self.KB_MODE_OFF)
        
    def SetDefaultMode(self):
        self._setMode(self.KB_MODE_DEFAULT)
        
    def SetPlainMode(self, mode_name):
        mode = self.plain_modes[mode_name]
        self._setMode(mode.to_bytes(1, 'little'))
        
    def SetNormalMode(self, zone1_color=(255, 255, 255), zone2_color=(255, 255, 255), zone3_color=(255, 255, 255)):
        self._setMode(self.KB_MODE_NORMAL)
        self._setZoneColorNormal(1, *zone1_color)
        self._setZoneColorNormal(2, *zone2_color)
        self._setZoneColorNormal(3, *zone3_color)
    
    def SetDualModeAdvanced(self, zone1=((255, 255, 255), (255, 255, 255), (0, 0, 0)), zone2=((255, 255, 255), (255, 255, 255), (0, 0, 0)), zone3=((255, 255, 255), (255, 255, 255), (0, 0, 0))):
        self._setDualModeZone(1, *zone1)
        self._setDualModeZone(2, *zone2)
        self._setDualModeZone(3, *zone3)
        
    def SetDualMode(self, color_a=(255, 255, 255), color_b=(255, 255, 255), color_fade_time=(0, 0, 0)):
        zone_setup = (color_a, color_b, color_fade_time)
        self.SetDualModeAdvanced(zone_setup, zone_setup, zone_setup)
    
    def __del__(self):
        self.dev.close()
