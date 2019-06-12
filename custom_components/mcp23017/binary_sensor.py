"""Support for binary sensor using I2C MCP23017 chip."""
import logging

import voluptuous as vol

from . import get_mcp
from homeassistant.components import rpi_gpio
from homeassistant.components.binary_sensor import (
    BinarySensorDevice, PLATFORM_SCHEMA)
from homeassistant.const import DEVICE_DEFAULT_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import (dispatcher_send,
                                      async_dispatcher_connect)

_LOGGER = logging.getLogger(__name__)

CONF_I2C_ADDRESS = 'i2c_address'
CONF_INVERT_LOGIC = 'invert_logic'
CONF_INTERRUPT = 'interrupt_port'
CONF_PINS = 'pins'
CONF_PULL_MODE = 'pull_mode'

DEFAULT_INVERT_LOGIC = False
DEFAULT_I2C_ADDRESS = 0x20
DEFAULT_PULL_MODE = 'UP'

_SENSORS_SCHEMA = vol.Schema({
    cv.positive_int: cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PINS): _SENSORS_SCHEMA,
    vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
    vol.Optional(CONF_INTERRUPT): cv.positive_int,
    vol.Optional(CONF_PULL_MODE, default=DEFAULT_PULL_MODE): vol.In(['UP', 'DOWN']),
    vol.Optional(CONF_I2C_ADDRESS, default=DEFAULT_I2C_ADDRESS):
    vol.Coerce(int),
})

DEVICE = 'mcp23017_binary_sensor_{}_{}_update'

async def async_setup_platform(hass, config, async_add_devices,
                               discovery_info=None):
    """Set up the MCP23017 binary sensors."""
    from RPi import GPIO

    pull_mode = config.get(CONF_PULL_MODE)
    invert_logic = config.get(CONF_INVERT_LOGIC)
    interrupt = config.get(CONF_INTERRUPT)
    i2c_address = config.get(CONF_I2C_ADDRESS)

    mcp = get_mcp(i2c_address)

    binary_sensors = []
    pins = config.get(CONF_PINS)

    for pin_num, pin_name in pins.items():
        pin = mcp.get_pin(pin_num)
        binary_sensors.append(MCP23017BinarySensor(
            pin_name, pin, pin_num, pull_mode, invert_logic,
            i2c_address, interrupt))

    async_add_devices(binary_sensors, True)

    def int_config(pins):
        """Returns a 16 bit number with the bit set for each pin."""
        gpinten = 0
        for pin in pins:
            gpinten |= 1 << pin
        return gpinten

    def update_sensors(port):
        for pin_num in mcp.int_flag:
            _LOGGER.debug("Dispatching MCP23017: {} on port: {} ".format(
                           DEVICE.format(i2c_address, pin_num),port))
            dispatcher_send(hass, DEVICE.format(i2c_address, pin_num))
        mcp.clear_ints()

    if interrupt:
        mcp.interrupt_enable = int_config(pins)
        mcp.interrupt_configuration = 0x0000 # Interrupt on any change
        mcp.io_control = 0x44 # Set interrupt as open drain and mirrored
        mcp.clear_ints() # Clear interrupts
            
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(interrupt, GPIO.IN, GPIO.PUD_UP)
        GPIO.add_event_detect(interrupt, GPIO.FALLING, callback=update_sensors,
                              bouncetime=10)


class MCP23017BinarySensor(BinarySensorDevice):
    """Represent a binary sensor that uses MCP23017."""

    def __init__(self, name, pin, pin_num, pull_mode, invert_logic,
                 i2c_address, interrupt):
        """Initialize the MCP23017 binary sensor."""
        import digitalio
        self._name = name or DEVICE_DEFAULT_NAME
        self._pin = pin
        self._pin_num = pin_num
        self._pull_mode = pull_mode
        self._invert_logic = invert_logic
        self._i2c_address = i2c_address
        self._interrupt = interrupt
        self._state = None
        self._pin.direction = digitalio.Direction.INPUT
        self._pin.pull = digitalio.Pull.UP

    @property
    def should_poll(self):
        """Return True if polling is needed."""
        if self._interrupt: return False

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the entity."""
        return self._state != self._invert_logic

    def update(self):
        """Update the GPIO state."""
        self._state = self._pin.value

    async def async_added_to_hass(self):
        """Register update signal handler."""
        async def async_update_state():
            """Update sensor state."""
            await self.async_update_ha_state(True)
        if self._interrupt:            
            _LOGGER.debug("Adding signal: {}".format(DEVICE.format(
                            self._i2c_address, self._pin_num)))
            async_dispatcher_connect(self.hass,
                                 DEVICE.format(self._i2c_address, self._pin_num),
                                 async_update_state)
