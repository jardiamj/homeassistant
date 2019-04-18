"""Support for I2C MCP23017 chip."""
import logging

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'mcp23017'


def get_mcp(i2c_address):
    """Returns an MCP23017 chip object."""
    import adafruit_mcp230xx
    import board
    import busio

    i2c = busio.I2C(board.SCL, board.SDA)
    mcp = adafruit_mcp230xx.MCP23017(i2c, address=i2c_address)
    return mcp

def get_pin(mcp, pin_number):
    """Returns an MCP23017 pin object."""
    return mcp.get_pin(pin_number)

def setup_output(pin):
    import digitalio
    pin.direction = digitalio.Direction.OUTPUT

def setup_input(pin):
    import digitalio
    pin.direction = digitalio.Direction.INPUT

async def read_input(pin):
    return pin.value
    
