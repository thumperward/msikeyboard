# MSI Keyboard Service
## Description

It is a service that controls certain types of keyboard backlights installed on some MSI laptops (e.g. MSI GT60 2PC). These keyboard usually have "Keyboard by SteelSeries" label.

## Functions

* Configure and use some (later - all) modes from SteelSeries app (on Windows) and also some undocumented (i.e. discovered by accident) modes
* React on lid close/open and sleep/resume events
* More functions later on

## Dependencies

* python3
* dbus
* python3-hidapi
* python3-dbus
* python3-yaml
* systemd (optional, if you want to install the service as described below)

## Installation 

1. Install this package from PyPI or from source using setup.py
2. Copy the file 'data/org.morozzz.MSIKeyboardService.conf' to directory '/etc/dbus-1/system.d/'
3. Copy the file 'data/msikeyboardd.service' to directory '/lib/systemd/system/'
4. In the root terminal (or with sudo), execute following commands:

> systemctl daemon-reload  
  systemctl reload dbus  
  systemctl enable msikeyboardd  
  systemctl start msikeyboardd

## Control methods

This service exposes several methods to DBus system bus:

* SetMode(t) -> b - selects backlight mode by index (i.e. by index in 'modes' configuration list), returns true if selected successfully
* SetDefaultMode() - selects default (i.e. bright white) backlight mode.
* SetOffMode() - selects off mode (i.e. no backlight at all).
* RestoreLastMode() -> b - restores last mode set by index. Helpful after SetDefaultMode and SetOffMode invocations.

Furthermore, the service connects to PropertiesChanged signal to react on lid events. When lid closes, backlight enters Off mode, when opens -- restores last mode set by index.

You can create your own tool that can control this service via DBus or use standard tool 'dbus-send' for the same purposes. For example, to set mode #0 (first mode from configuration), you can invoke dbus-send as follows:

> dbus-send --system --dest="org.morozzz.MSIKeyboardService" --type=method_call /org/morozzz/MSIKeyboardService org.morozzz.MSIKeyboardService.SetMode uint64:0

As Ubuntu user I bound keys Ctrl-Alt-{0-9} to SetMode({0-9}) invocations, Ctrl-Alt-- ('minus', key that comes after '0' key) to SetOffMode invocation, Ctrl-Alt-= ('equals', the key that comes after 'minus' and before 'backspace') to SetDefaultMode invoacation and Ctrl-Alt-Backspace to RestoreLastMode invocation via dbus-send, using System Settings -- Keyboard -- Shortcuts settings.

## Configuration

Configuration is stored in '/etc/msikeyboard/config.yaml' file in [YAML](https://en.wikipedia.org/wiki/YAML) serialization format. Configuration keys:

* default_index (int) - Mode index that will be set immediately after service starts
* handle_lid (bool) - Handle lid events
* handle_sleep (bool) - Handle sleep events
* resume_to_connect_delay (float) - Delay between connection attempts in 'resume from sleep' event handler
* modes (list) - List of mode configurations
    * type (str) - Mode type name
    * config (dict) - Mode configuration

Available modes:

* Off (note quotes) - Disabled backlight
    * No (empty) configuration
* Default - Bright white backlight
    * No (empty) configuration
* Normal - Colored backlight, each zone (left, middle and right) has its own color
    * each zone has dict of three keys - 'r', 'g', 'b' that stand for red, green and blue color intensity (0-255)
    * zones have names 'left', 'middle' and 'right'
* DualColor - Slow transition from first color to second:
    * 'color_a' - first color
    * 'color_b' - second color
    * 'fade_times' - transition time periods (for each color)
    * each key has dict of three keys - 'r', 'g', 'b', that stand for red, green and blue color intensity
    * times are approximately in seconds (0 - fastest, but not immediate, 255 - slowest)
* Gaming - only left zone illuminated:
    * dict of three keys - 'r', 'g', 'b', that stand for red, green and blue color intensity
* Breathing - Colored backlight, fading to black and vice versa:
    * three zones named 'left', 'middle' and 'right'
    * each zone has dict of two keys - 'color' and 'fade_times'
    * 'color' and 'fade_times' each have dict of three keys - 'r', 'g', 'b', that stand for red, green and blue color intensity / fade times
* Wave - Colored backlight, one zone at a time, fading to black and appearing again in a sequence, left-to-right:
    * parameters defined in analogy to "Breathing" mode
* Audio - Backlight responding to sounds from built-in speakers. No idea how it works, but is seems to me that for normal functioning on Linux this mode needs some black magic.
    * No (empty) configuration

## TODO:

* Expose DualColorAdvanced mode (like DualColor, but each zone has different colors/times, msikbapi already has appropriate methods)
* Expose 'plain' modes (16-28, looks like plain one-color backlight, also changes behavior of Normal mode)
* Explore modes 8,9 and 11-15 (8 looks like DualColor, 9 looks like Waves but it needs thorough research)
* Move service daemon from root to less privileged system user
* Add console daemon control tool
* Add GUI daemon control tool?
