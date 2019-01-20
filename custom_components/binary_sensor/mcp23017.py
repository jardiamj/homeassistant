"""
Support for binary sensor using MCP23017 on Raspberry Pi.
For more details about this platform, please refer to the documentation at
### Link to docs ###
"""
import logging

import voluptuous as vol
import asyncio

from homeassistant.components.binary_sensor import (
    BinarySensorDevice, PLATFORM_SCHEMA)
from homeassistant.const import DEVICE_DEFAULT_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity, async_generate_entity_id
from homeassistant.helpers.event import async_track_state_change

REQUIREMENTS = ['RPi.GPIO==0.6.5',
                'adafruit-blinka==1.2.1',
                'adafruit-circuitpython-mcp230xx==1.1.2']

_LOGGER = logging.getLogger(__name__)

CONF_BOUNCETIME = 'bouncetime'
CONF_INVERT_LOGIC = 'invert_logic'
CONF_PINS = 'pins'
CONF_PULL_MODE = 'pull_mode'

DEFAULT_BOUNCETIME = 50
DEFAULT_INVERT_LOGIC = False
DEFAULT_PULL_MODE = 'UP'

_SENSORS_SCHEMA = vol.Schema({
    cv.positive_int: cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PINS): _SENSORS_SCHEMA,
    vol.Optional(CONF_BOUNCETIME, default=DEFAULT_BOUNCETIME): cv.positive_int,
    vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
    vol.Optional(CONF_PULL_MODE, default=DEFAULT_PULL_MODE): cv.string,
})


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the Raspberry PI GPIO devices."""
    
    import board
    import busio
    import adafruit_mcp230xx
    i2c = busio.I2C(board.SCL, board.SDA)
    mcp = adafruit_mcp230xx.MCP23017(i2c)
    
    pull_mode = config.get(CONF_PULL_MODE)
    bouncetime = config.get(CONF_BOUNCETIME)
    invert_logic = config.get(CONF_INVERT_LOGIC)
    
    binary_sensors = []
    pins = config.get('pins')
    
    for pin_num, pin_name in pins.items():
        pin = mcp.get_pin(pin_num)
        binary_sensors.append(mcp23017BinarySensor(
            hass, pin_name, pin, pull_mode, bouncetime, invert_logic))
            
    async_add_devices(binary_sensors, True)

class mcp23017BinarySensor(BinarySensorDevice):
    """Represent a binary sensor that uses MCP23017 connected to a Raspberrypi"""

    def __init__(self, hass, name, pin, pull_mode, bouncetime, invert_logic):
        """Initialize the RPi binary sensor."""
        
        self._name = name or DEVICE_DEFAULT_NAME
        self._pin = pin
        self._pull_mode = pull_mode
        self._bouncetime = bouncetime
        self._invert_logic = invert_logic
        self._state = None
        self.hass = hass
        
        import digitalio
        
        self._pin.direction = digitalio.Direction.INPUT
        self._pin.pull = digitalio.Pull.UP

        async def async_added_to_hass(self):
            """Register callbacks."""
            @callback
            def async_sensor_state_listener(entity, old_state, new_state):
                """Called when the target device changes state."""
                hass.async_add_job(self.async_update_ha_state, True)
            
            async_track_state_change(
            self.hass, self._name, async_sensor_state_listener)

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def is_on(self):
        """Return the state of the entity."""
        return self._state != self._invert_logic
        
    @callback
    def _update_data(self):
        """Update the state."""
        self.async_schedule_update_ha_state(True)
       
    async def async_update(self):
        """Update the GPIO state."""
        self._state = self._pin.value
