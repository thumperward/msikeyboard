import hidapi as hid

class MSIKeyboard:
    vendorID = 0x1770
    productID = 0xFF00
    serial = "MSI EPF USB"
    
    REPORT_ID = b'\x01'
    PREAMBLE = b'\x02'
    LAST_BYTE = b'\x00'
    
    CMD_SET_MODE = b'\x41'
    CMD_SET_ZONE_COLOR = b'\x40'
    CMD_SET_MODE_ATTRIBUTE = b'\x44'
    
    KB_MODE_OFF = b'\x00'
    KB_MODE_NORMAL = b'\x01'
    KB_MODE_GAMING = b'\x02'
    KB_MODE_BREATHE = b'\x03'
    KB_MODE_AUDIO = b'\x04'
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
    
    def Connect(self):
        self.dev = hid.Device(vendor_id=self.vendorID, product_id=self.productID, serial_number=self.serial)
    
    def Disconnect(self):
        self.dev.close()
    
    def _writeToDevice(self, report):
        try:
            self.dev.send_feature_report(report, self.REPORT_ID)
        except OSError as e:
            print("Device write failed: " + str(e))
            self.Connect()
            self.dev.send_feature_report(report, self.REPORT_ID)
            print("Device write succeeded")
    
    def _sendCommand(self, command, arg1=b'\x00', arg2=b'\x00', arg3=b'\x00', arg4=b'\x00'):
        report = self.PREAMBLE + command + arg1 + arg2 + arg3 + arg4 + self.LAST_BYTE
        self._writeToDevice(report)
        
    def _setMode(self, mode):
        self._sendCommand(self.CMD_SET_MODE, mode)
        
    def _setZoneColor(self, zone, r, g, b):
        self._sendCommand(self.CMD_SET_ZONE_COLOR, zone.to_bytes(1, 'little'), r.to_bytes(1, 'little'), g.to_bytes(1, 'little'), b.to_bytes(1, 'little'))
        
    def _setModeAttribute(self, attribute, arg1=0, arg2=0, arg3=0):
        self._sendCommand(self.CMD_SET_MODE_ATTRIBUTE, attribute.to_bytes(1, 'little'), arg1.to_bytes(1, 'little'), arg2.to_bytes(1, 'little'), arg3.to_bytes(1, 'little'))
    
    def _setCompositeModeZone(self, mode, zone, color_a=(255, 255, 255), color_b=(255, 255, 255), color_fade_time=(0, 0, 0)):
        zidx = (zone-1) * 3 + 1
        self._setModeAttribute(zidx + 0, *color_a)
        self._setModeAttribute(zidx + 1, *color_b)
        self._setModeAttribute(zidx + 2, *color_fade_time)
        self._setMode(mode)

    def _setDualModeZone(self, zone, color_a=(255, 255, 255), color_b=(255, 255, 255), color_fade_time=(0, 0, 0)):
        self._setCompositeModeZone(self.KB_MODE_DUAL, zone, color_a, color_b, color_fade_time)
        
    def _setBreathingModeZone(self, zone, color_a=(255, 255, 255), color_b=(255, 255, 255), color_fade_time=(0, 0, 0)):
        self._setCompositeModeZone(self.KB_MODE_BREATHE, zone, color_a, color_b, color_fade_time)
    
    def _setWaveModeZone(self, zone, color_a=(255, 255, 255), color_b=(255, 255, 255), color_fade_time=(0, 0, 0)):
        self._setCompositeModeZone(self.KB_MODE_WAVE, zone, color_a, color_b, color_fade_time)
    
    def SetOffMode(self):
        self._setMode(self.KB_MODE_OFF)
        
    def SetDefaultMode(self):
        self._setMode(self.KB_MODE_DEFAULT)
        
    def SetPlainMode(self, mode_name):
        mode = self.plain_modes[mode_name]
        self._setMode(mode.to_bytes(1, 'little'))
        
    def SetGamingMode(self, zone_color_r, zone_color_g, zone_color_b):
        self._setMode(self.KB_MODE_GAMING)
        self._setZoneColor(1, zone_color_r, zone_color_g, zone_color_b)
        
    def SetNormalMode(self, zone1_color=(255, 255, 255), zone2_color=(255, 255, 255), zone3_color=(255, 255, 255)):
        self._setMode(self.KB_MODE_NORMAL)
        self._setZoneColor(1, *zone1_color)
        self._setZoneColor(2, *zone2_color)
        self._setZoneColor(3, *zone3_color)
    
    def SetDualModeAdvanced(self, zone1=((255, 255, 255), (255, 255, 255), (0, 0, 0)), zone2=((255, 255, 255), (255, 255, 255), (0, 0, 0)), zone3=((255, 255, 255), (255, 255, 255), (0, 0, 0))):
        self._setDualModeZone(1, *zone1)
        self._setDualModeZone(2, *zone2)
        self._setDualModeZone(3, *zone3)
        
    def SetDualMode(self, color_a=(255, 255, 255), color_b=(255, 255, 255), color_fade_time=(0, 0, 0)):
        zone_setup = (color_a, color_b, color_fade_time)
        self.SetDualModeAdvanced(zone_setup, zone_setup, zone_setup)
    
    def SetBreathingModeAdvanced(self, zone1=((255, 255, 255), (255, 255, 255), (0, 0, 0)), zone2=((255, 255, 255), (255, 255, 255), (0, 0, 0)), zone3=((255, 255, 255), (255, 255, 255), (0, 0, 0))):
        self._setBreathingModeZone(1, *zone1)
        self._setBreathingModeZone(2, *zone2)
        self._setBreathingModeZone(3, *zone3)
    
    def SetBreathingMode(self, zone1_color=(255, 255, 255), zone1_time=(0, 0, 0), zone2_color=(255, 255, 255), zone2_time=(0, 0, 0), zone3_color=(255, 255, 255), zone3_time=(0, 0, 0)):
        zone1_setup = (zone1_color, (0, 0, 0), zone1_time)
        zone2_setup = (zone2_color, (0, 0, 0), zone2_time)
        zone3_setup = (zone3_color, (0, 0, 0), zone3_time)
        self.SetBreathingModeAdvanced(zone1_setup, zone2_setup, zone3_setup)
        
    def SetWaveModeAdvanced(self, zone1=((255, 255, 255), (255, 255, 255), (0, 0, 0)), zone2=((255, 255, 255), (255, 255, 255), (0, 0, 0)), zone3=((255, 255, 255), (255, 255, 255), (0, 0, 0))):
        self._setWaveModeZone(1, *zone1)
        self._setWaveModeZone(2, *zone2)
        self._setWaveModeZone(3, *zone3)
        
    def SetWaveMode(self, zone1_color=(255, 255, 255), zone1_time=(0, 0, 0), zone2_color=(255, 255, 255), zone2_time=(0, 0, 0), zone3_color=(255, 255, 255), zone3_time=(0, 0, 0)):
        zone1_setup = (zone1_color, (0, 0, 0), zone1_time)
        zone2_setup = (zone2_color, (0, 0, 0), zone2_time)
        zone3_setup = (zone3_color, (0, 0, 0), zone3_time)
        self.SetWaveModeAdvanced(zone1_setup, zone2_setup, zone3_setup)
    
    def SetAudioMode(self):
        self._setMode(self.KB_MODE_AUDIO)
    
#    def __del__(self):
#        self.dev.close()
