# Custom Components for Home Assistant 

This is a repository for my custom components for Home Assistant.

## Custom Components
- mcp23017 binary_sensor:
  mcp23017 is and I/O expander that I am using to connect my doors and windows sensors (reed sensors) to a Raspberry Pi running Home Assistant.
- mcp23017 switch:

## Getting Started

To use these customs components you need to create a custom_components directory inside you Home Assistant configuration directory. In a Raspbian installation it will be ~/.homeassistant.
You will be placing the components inside this directory.

### Prerequisites

The mcp23017 communicates with the Raspberry Pi through I2C serial communication. I2C on Raspbian is disabled by default so you will have to enable it.
This is a good guide with screenshots on how to enable I2C on Raspbian: https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c

You will also have to add the Home Assistant user to the i2c group:

```
sudo usermod -a -G i2c homeassistant
```
### Requirements

Requirements in Home Assistant are installed on the fly but it's good for you to know that mcp23017 component uses and therefore requires the following python modules:
- RPi.GPIO
- adafruit-blinka
- adafruit-circuitpython-mcp230xx

### Installing mcp23017 binary_sensor

Place the contents of mcp23017 directory inside ~/.homeassistant/custom_components/mcp23017
The easiest way is using svn, if you don't have it installed you can install it with:

```shell
sudo apt install subversion
```
Now, you can do the following:

```shell
$ ssh your_user@raspberrypi
$ sudo -u homeassistant -H -s
$ cd ~/.homeassistant
$ mkdir custom_components/
$ cd custom_components/
$ svn checkout https://github.com/jardiamj/homeassistant/trunk/custom_components/mcp23017
```
To use the mcp23017 binary sensor in your installation, add the following to your configuration.yaml file:

```yaml
# Example configuration.yaml entry
binary_sensor:
  - platform: mcp23017
    i2c_address: 0x20
    scan_interval: 1
    pins:
      0: Living Room Window
      1: Kitchen Window
      2: Front Door
```
To use the mcp23017 switch components in your installation, add the following to your configuration.yaml file:

```yaml
# Example configuration.yaml entry
switch:
  - platform: mcp23017
    i2c_address: 0x20
    pins:
      11: Fan Office 
      12: Light Desk 
```

{% configuration %}
pins:
  description: List of used pins.
  required: true
  type: map
  keys:
    "pins: name":
      description: The MCP23017 pin numbers and corresponding names.
      required: true
      type: string
i2c_address:
  description: i2c address of MCP23017 chip.
  required: false
  type: integer
  default: "`0x20`"
scan_interval:
  description: Interval to scan for sensor state changes in seconds.
  required: false
  type: integer
  default: "`15`"
invert_logic:
  description: If `true`, inverts the output logic to ACTIVE LOW.
  required: false
  type: boolean
  default: "`false` (ACTIVE HIGH)"
pull_mode:
  description: >
    Type of internal pull resistor to use.
    Options are `UP` - pull-up resistor and `DOWN` - pull-down resistor.
  required: false
  type: string
  default: "`UP`"
{% endconfiguration %}

NOTE: MCP23017 only has internal pull-up resistors, if you want to use pull-down you will have to wire your own pull-down resistors.

