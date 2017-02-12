#!/usr/bin/python3 -u

import dbus
import dbus.service
from gi.repository import GLib
import yaml
import msikbapi
import signal

CONFIG_PATH = '/etc/msikeyboard/'
CONFIG_NAME = 'config.yaml'

GLib.threads_init()
loop = GLib.MainLoop()

from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

class AbstractKeyboardMode:
    def setMode(self, keyboard_object):
        return NotImplemented
        
    def to_dict(self):
        return NotImplemented
        
    @classmethod
    def from_dict(cls, dict):
        return NotImplemented


class OffKeyboardMode(AbstractKeyboardMode):
    def __init__(self):
        pass
        
    def setMode(self, keyboard_object):
        keyboard_object.SetOffMode()
        
    def to_dict(self):
        return {}
        
    @classmethod
    def from_dict(cls, dict):
        return cls()


class DefaultKeyboardMode(AbstractKeyboardMode):
    def __init__(self):
        pass
        
    def setMode(self, keyboard_object):
        keyboard_object.SetDefaultMode()
        
    def to_dict(self):
        return {}
        
    @classmethod
    def from_dict(cls, dict):
        return cls()


class NormalKeyboardMode(AbstractKeyboardMode):
    def __init__(self, zone1_color, zone2_color, zone3_color):
        self.zone1 = zone1_color
        self.zone2 = zone2_color
        self.zone3 = zone3_color
    
    def setMode(self, keyboard_object):
        keyboard_object.SetNormalMode(self.zone1, self.zone2, self.zone3)
        
    def to_dict(self):
        return {'left': {'r': self.zone1[0], 'g': self.zone1[1], 'b': self.zone1[2]}, 
                'middle': {'r': self.zone2[0], 'g': self.zone2[1], 'b': self.zone2[2]}, 
                'right': {'r': self.zone3[0], 'g': self.zone3[1], 'b': self.zone3[2]}}
                
    @classmethod
    def from_dict(cls, dict):
        zone1_dict = dict['left']
        zone2_dict = dict['middle']
        zone3_dict = dict['right']
        zone1 = (zone1_dict['r'], zone1_dict['g'], zone1_dict['b'])
        zone2 = (zone2_dict['r'], zone2_dict['g'], zone2_dict['b'])
        zone3 = (zone3_dict['r'], zone3_dict['g'], zone3_dict['b'])
        return cls(zone1, zone2, zone3)


class DualColorKeyboardMode(AbstractKeyboardMode):
    def __init__(self, first_color, second_color, color_transition_times):
        self.color_a = first_color
        self.color_b = second_color
        self.color_fade_time = color_transition_times
        
    def setMode(self, keyboard_object):
        keyboard_object.SetDualMode(self.color_a, self.color_b, self.color_fade_time)
        
    def to_dict(self):
        return {'color_a': {'r': self.color_a[0], 'g': self.color_a[1], 'b': self.color_a[2]}, 
                'color_b': {'r': self.color_b[0], 'g': self.color_b[1], 'b': self.color_b[2]}, 
                'fade_times': {'r': self.color_fade_time[0], 'g': self.color_fade_time[1], 'b': self.color_fade_time[2]}}
                
    @classmethod
    def from_dict(cls, dict):
        colora_dict = dict['color_a']
        colorb_dict = dict['color_b']
        fade_dict = dict['fade_times']
        colora = (colora_dict['r'], colora_dict['g'], colora_dict['b'])
        colorb = (colorb_dict['r'], colorb_dict['g'], colorb_dict['b'])
        fade = (fade_dict['r'], fade_dict['g'], fade_dict['b'])
        return cls(colora, colorb, fade)


class MSIKeyboardService(dbus.service.Object):
    SERVICE_NAME = 'org.morozzz.MSIKeyboardService'
    SERVICE_PATH = '/org/morozzz/MSIKeyboardService'
    SERVICE_NATIVE_INTERFACE = 'org.morozzz.MSIKeyboardService'
    
    PROPS_INTERFACE = 'org.freedesktop.DBus.Properties'
    PROPS_CHANGED_SIGNAL = 'PropertiesChanged'
    UPOWER_NAME = 'org.freedesktop.UPower'
    
    kbmodes = {
        'Off': OffKeyboardMode, 
        'Default': DefaultKeyboardMode, 
        'Normal': NormalKeyboardMode, 
        'DualColor': DualColorKeyboardMode
    }
    
    kbmodes_rev = {value: key for key, value in kbmodes.items()}
    
    def __init__(self, keyboard_object, config_file_name=None):
        self.kb = keyboard_object
        self.modes = []
        self.configfile = config_file_name
        self.isConfigChanged = False
        self.isHandleLid = False
        self.defModeIndex = 0
        self.curModeIndex = None
        bus = dbus.SystemBus()
        bus.request_name(self.SERVICE_NAME)
        bus_name = dbus.service.BusName(self.SERVICE_NAME, bus=bus)
        dbus.service.Object.__init__(self, bus_name, self.SERVICE_PATH)
    
    def LoadDefaultConfig(self):
        self.modes = [
            OffKeyboardMode(), 
            DefaultKeyboardMode(), 
            NormalKeyboardMode((255, 0, 0), (0, 255, 0), (0, 0, 255)), 
            DualColorKeyboardMode((255, 0, 0), (0, 255, 0), (3, 3, 3)), 
        ]
        self.defModeIndex = 0
        self.isHandleLid
        self.isConfigChanged = True
    
    def LoadDefaultConfigConditional(self):
        if self.modes:
            print("Leaving current configuration")
        else:
            print("Loading default config")
            self.LoadDefaultConfig()
    
    def PropsChangedHandler(self, source, props_dict, unused):
        if source == self.UPOWER_NAME:
            if 'LidIsClosed' in props_dict:
                isLidClosed = props_dict['LidIsClosed']
                if isinstance(isLidClosed, dbus.Boolean):
                    self.LidActionHandler(bool(isLidClosed))
                else:
                    print('Warning: property LidIsClosed has unusual type ' + str(type(isLidClosed)) + ", skipping signal")
    
    def LidActionHandler(self, isLidClosed):
        if isLidClosed is True:
            print("Lid close detected, turning off keyboard backlight")
            self.SetOffModeImpl()
        else:
            print("Lid open detected, restoring keyboard backlight")
            self.RestoreModeImpl()
            
    def _connectPropsChangedHandler(self):
        bus = dbus.SystemBus()
        bus.add_signal_receiver(self.PropsChangedHandler, self.PROPS_CHANGED_SIGNAL, self.PROPS_INTERFACE)
    
    def LoadConfig(self):
        if self.configfile is not None:
            print("Loading config from file " + self.configfile)
            try:
                config_file = open(self.configfile, 'r')
                config_dict = yaml.load(config_file)
                config_file.close()
                try:
                    self.defModeIndex = int(config_dict['default_index'])
                except (KeyError, TypeError, ValueError):
                    print("Key 'default_index' not found or invalid, proceeding with default value '" + self.defModeIndex + "'")
                try:
                    self.isHandleLid = bool(config_dict['handle_lid'])
                    if self.isHandleLid:
                        self._connectPropsChangedHandler()
                except (KeyError, TypeError, ValueError):
                    print("Key 'handle_lid' not found or invalid, not handling lid events")
                modes_list = config_dict['modes']
                modes = []
                for mode_description in modes_list:
                    try:
                        mode_type_name = mode_description['type']
                        mode_dict = mode_description['config']
                    except KeyError as e:
                        raise RuntimeError("Can't find key " + str(e) + " in one of the mode descriptions")
                    except TypeError:
                        raise RuntimeError("Invalid config block type for mode description (must be mapping)")
                    try:
                        mode_type = self.kbmodes[mode_type_name]
                    except KeyError:
                        raise RuntimeError("Unknown mode '" + mode_type_name + "'")
                    try:
                        mode = mode_type.from_dict(mode_dict)
                    except KeyError as e:
                        raise RuntimeError("Invalid config for mode '" + mode_type_name + "': can't find key '" + str(e) + "'")
                    except TypeError:
                        raise RuntimeError("Invalid config for mode '" + mode_type_name + "': invalid config block type")
                    modes.append(mode)
                self.modes = modes
                print("Configuration loaded successfully")
                return True
            except (FileNotFoundError, PermissionError):
                print("Can't open configuration file '" + str(self.configfile) + "'")
            except KeyError as e:
                print("Invalid configuration file format: can't find key '" + str(e) + "'")
            except TypeError:
                print("Invalid configuration file format: invalid block type")
            except RuntimeError as e:
                print("Invalid configuration file: " + str(e))
            except yaml.YAMLError as e:
                print("Incorrect configuration file: " + str(e))
            self.LoadDefaultConfigConditional()
            return False
        else:
            print("Config file name is not set")
            self.LoadDefaultConfigConditional()
            return False
            
    def _getConfigDict(self):
        modes_list = []
        for mode in self.modes:
            mode_type_name = self.kbmodes_rev[type(mode)]
            mode_dict = mode.to_dict()
            mode_description = {"type": mode_type_name, "config": mode_dict}
            modes_list.append(mode_description)
        return {'modes': modes_list, 'default_index': self.defModeIndex, 'handle_lid': self.isHandleLid}
            
    def SaveConfig(self, Forced=False):
        if self.configfile is None:
            print("Config file name is not set, not saving")
            return False
        elif not Forced and self.isConfigChanged is False:
            print("Configuration not changed, not saving")
            return False
        else:
            print("Saving configuration to file '" + self.configfile + "'")
            try:
                config_file = open(self.configfile, "w")
                config_dict = self._getConfigDict()
                yaml.dump(config_dict, config_file)
                config_file.close()
                print("Configuration successfully saved")
                return True
            except (FileNotFoundError, PermissionError):
                print("Can't open file " + self.configfile + " for write, not saving config")
                return False
            
    def SetModeImpl(self, mode_index):
        try:
            mode = self.modes[mode_index]
            mode.setMode(self.kb)
            self.curModeIndex = mode_index
            print("Selected mode " + str(mode_index) + ": " + self.kbmodes_rev[type(mode)])
            return True
        except IndexError:
            print("Warning: Mode index '" + str(mode_index) + "' is out of range, not setting mode")
            return False
            
    def SetDefaultModeImpl(self):
        self.kb.SetDefaultMode()
        print("Selected Default mode")
        
    def SetOffModeImpl(self):
        self.kb.SetOffMode()
        print("Selected Off mode")
        
    def RestoreModeImpl(self):
        if self.curModeIndex is None:
            print("Last mode index is not set, nothing to restore")
            return False
        else:
            try:
                mode = self.modes[self.curModeIndex]
                mode.setMode(self.kb)
                print("Restored mode " + str(self.curModeIndex) + ": " + self.kbmodes_rev[type(mode)])
                return True
            except IndexError:
                print("Warning: Last mode index '" + str(self.curModeIndex) + "' is out of range, unsetting it")
                self.curModeIndex = None
                return False
            
    @dbus.service.method(dbus_interface=SERVICE_NATIVE_INTERFACE, in_signature="t", out_signature="b")
    def SetMode(self, index):
        return self.SetModeImpl(index)
        
    @dbus.service.method(dbus_interface=SERVICE_NATIVE_INTERFACE, in_signature="", out_signature="")
    def SetDefaultMode(self):
        self.SetDefaultModeImpl()
        
    @dbus.service.method(dbus_interface=SERVICE_NATIVE_INTERFACE, in_signature="", out_signature="")
    def SetOffMode(self):
        self.SetOffModeImpl()
        
    @dbus.service.method(dbus_interface=SERVICE_NATIVE_INTERFACE, in_signature="", out_signature="t")
    def GetModesNumber(self):
        return len(self.modes)
        
    @dbus.service.method(dbus_interface=SERVICE_NATIVE_INTERFACE, in_signature="", out_signature="bt")
    def GetLastModeIndex(self):
        return (True, self.curModeIndex) if self.curModeIndex is not None else (False, 0)
        
    @dbus.service.method(dbus_interface=SERVICE_NATIVE_INTERFACE, in_signature="", out_signature="b")
    def ReloadConfig(self):
        return self.LoadConfig()
        
    @dbus.service.method(dbus_interface=SERVICE_NATIVE_INTERFACE, in_signature="", out_signature="b")
    def ForceSaveConfig(self):
        return self.SaveConfig(True)
    
    @dbus.service.method(dbus_interface=SERVICE_NATIVE_INTERFACE, in_signature="", out_signature="b")
    def RestoreLastMode(self):
        return self.RestoreModeImpl()
    
    def OnLoad(self):
        self.LoadConfig()
        self.SetModeImpl(self.defModeIndex)
    
    def OnExit(self):
        self.SaveConfig()
        self.kb.SetOffMode()


def InitSignal(actor):
    def signal_action(signal):
        if signal == 1:
            print(("Got signal SIGHUP(1)"))
            actor.LoadConfig()
            return
        elif signal == 2:
            print(("Got signal SIGINT(2)"))
        elif signal == 15:
            print(("Got signal SIGTERM(15)"))
        else:
            print(("Got unregistered signal " + str(signal)))
            return
        actor.OnExit()
        loop.quit()

    def idle_handler(*args):
        print("Python signal handler activated")
        GLib.idle_add(signal_action, priority=GLib.PRIORITY_HIGH)

    def handler(*args):
        print("GLib signal handler activated")
        signal_action(args[0])

    def install_glib_handler(sig):
        unix_signal_add = None

        if hasattr(GLib, "unix_signal_add"):
            unix_signal_add = GLib.unix_signal_add
        elif hasattr(GLib, "unix_signal_add_full"):
            unix_signal_add = GLib.unix_signal_add_full

        if unix_signal_add:
            print(("Register GLib signal handler: %r" % sig))
            unix_signal_add(GLib.PRIORITY_HIGH, sig, handler, sig)
        else:
            print("Can't install GLib signal handler, too old gi.")

    SIGS = [getattr(signal, s, None) for s in "SIGINT SIGTERM SIGHUP".split()]
    for sig in [_f for _f in SIGS if _f]:
        print(("Register Python signal handler: %r" % sig))
        signal.signal(sig, idle_handler)
        GLib.idle_add(install_glib_handler, sig, priority=GLib.PRIORITY_HIGH)


if __name__ == "__main__":
    keyboard = msikbapi.MSIKeyboard()
    service = MSIKeyboardService(keyboard, CONFIG_PATH + CONFIG_NAME)
    service.OnLoad()
    InitSignal(service)
    loop.run()
    print("Application exited.")
