#!/usr/bin/env python3

import argparse
import logging
import socket
import signal
import sys
import time

from config import read_config

from logger import logger
from joystick import Joystick

# dictionary of all the xbox controller buttons and controls. By enabling or disabling
# the controls, you can control how much extra traffic is sent down to the XRP.
controls = {
    'ButtonA':        { 'type': 'BUTTON', 'enabled': True },
    'ButtonB':        { 'type': 'BUTTON', 'enabled': True  },
    'ButtonX':        { 'type': 'BUTTON', 'enabled': True  },
    'ButtonY':        { 'type': 'BUTTON', 'enabled': True  },
    'LeftBumper':     { 'type': 'BUTTON', 'enabled': True  },
    'RightBumper':    { 'type': 'BUTTON', 'enabled': True  },
    'Select':         { 'type': 'BUTTON', 'enabled': True  },
    'Start':          { 'type': 'BUTTON', 'enabled': True  },
    'LeftThumb':      { 'type': 'BUTTON', 'enabled': True  },
    'RightThumb':     { 'type': 'BUTTON', 'enabled': True  },
    'LeftJoystickX':  { 'type': 'AXIS',   'enabled': True  },
    'LeftJoystickY':  { 'type': 'AXIS',   'enabled': True  },
    'LeftTrigger':    { 'type': 'AXIS',   'enabled': True  },
    'RightJoystickX': { 'type': 'AXIS',   'enabled': True  },
    'RightJoystickY': { 'type': 'AXIS',   'enabled': True  },
    'RightTrigger':   { 'type': 'AXIS',   'enabled': True  },
    'HatX':           { 'type': 'AXIS',   'enabled': True  },
    'HatY':           { 'type': 'AXIS',   'enabled': True  }
}

#
# class to implement the XRP controller. This class is derived from the Joystick class
# and supports an Xbox Controller connected via USB to a Raspberry Pi
#
class XrpController(Joystick):
    def __init__(self, path=None, socket_type='UDP', host='', team_number=9999):
        super().__init__(path)

        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

        self.host = host
        self.port = team_number
        self.socket_type = socket_type

        # create a socket based on the requested type
        if self.socket_type == 'UDP':
            self.socket = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )

    def shutdown( self, *args ):
        logger.info( 'Shutdown complete.' )

        sys.exit(0)

    def send_event( self, event ):
        command = None
        name = event['name']
        try:
            control = controls[name]

            if control.get('enabled', False) == True:
                if control['type'] == 'AXIS':
                    # for the axis type, send the value rounded to the nearest 2 decimal points
                    value = event['rounded_value']
                    command = '%s:%s:%f' % ('Event',name, value) 
                elif control['type'] == 'BUTTON':
                    # for the button type, send the value reported by the button (1:PRESSED or 0:RELEASED)
                    value = event['value']
                    command = '%s:%s:%d' % ('Event',name, value) 
                else:
                    logger.error( 'Unknown Event Type: %s' % name )

                if command:
                    logger.debug( 'Sending: %s' % command )
                    if self.socket_type == 'UDP':
                        self.socket.sendto( command.encode('utf-8'), (self.host,self.port) )

        except KeyError:
            pass

    def joystick_control(self):
        for event in self.gamepad.read_loop():
            decoded_event = self.decode_event( event )
            self.send_event( decoded_event )

if __name__ == '__main__':

    #
    # parse out the command arguments
    #
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true', dest='debug', default=False)
    parser.add_argument('-c', '--config', action='store', dest='config', default='xrpconfig.json')
    parser.add_argument('-s', '--socket', action='store', dest='socket_type', default=None)
    parser.add_argument('-t', '--team', action='store', dest='team', default=None)
    parser.add_argument('-x', '--xrp', action='store', dest='xrp_ipaddr', default=None)
    options = parser.parse_args()

    #
    # Read the config file
    config = read_config( filename=options.config )

    # set the log level to debug if requested
    if options.debug or config.get('debug',False) == True:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # retrieve the XRP IP server address and port number (team) from config or
    # from the command line
    if options.xrp_ipaddr:
        xrp_ipaddr = options.xrp_ipaddr
    else:
        xrp_ipaddr = config.get('xrp_ipaddr', 'localhost')

    if options.team:
        team = options.team
    else:
        team = config.get('team', 9999)

    if options.socket_type:
        socket_type = options.socket_type.upper()
    else:
        socket_type = config.get('socket_type', 'UDP').upper()

    #
    # Create the XRP controller instance
    controller = XrpController(socket_type=socket_type, host=xrp_ipaddr, team_number=team)

    try:
        # invoke the controller type as configured. Initially, an Xbox Controller is supported,
        # but other controller methods will be added over time
        if config['controller'] == 'joystick':
            controller.joystick_control()
        else:
            logger.error( 'ERROR: No Controller Type Specified' )
            sys.exit(1)

    except KeyboardInterrupt:
        controller.shutdown();

