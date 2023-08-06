#!/usr/bin/env python3

import argparse
import logging
import ntcore
import time
import signal
import sys

from enum import Enum, auto


from bling import Bling
import bling_patterns

from config import read_config
from logger import logger
from joystick import Joystick
from lidar import Lidar

class LidarStates(Enum):
    INITIAL = auto()
    ACQUIRING = auto()
    ACQUIRED = auto()
    FOLLOWING = auto()
    STOPPED = auto()
    TERMINATING = auto()
    TERMINATED = auto()

class FrcController(Joystick):
    def __init__(self, path=None, team_number=9999):
        super().__init__(path)

        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

        self.inst = ntcore.NetworkTableInstance.getDefault()
        self.inst.startClient4('Test client')
        self.inst.setServerTeam(team_number) 

        self.table = self.inst.getTable("RobotRemoteControl")
        self.publishers = {}
        for button in list(self.BUTTONS.values()):
            self.publishers[button['name']] = self.table.getIntegerTopic(button['name']).publish()
        for axis in list(self.AXIS_TYPES.values()):
            self.publishers[axis['name']] = self.table.getDoubleTopic(axis['name']).publish()

        self.lidar = None
        self.lidar_state = LidarStates.INITIAL
        
        self.bling = None

        self.curr_turning_speed = 0.0
        self.turning_noupdates = 0
        self.curr_moving_speed = 0.0
        self.moving_noupdates = 0

    def shutdown( self, *args ):
        if self.lidar:
            logger.info( 'Terminating LIDAR Session' )
            self.set_lidar_state( LidarStates.TERMINATING)
            self.lidar.cancel()

            logger.info( 'Shutting down LIDAR' )
            controller.lidar.terminate()

        time.sleep(2)
        self.set_lidar_state( LidarStates.TERMINATED )
        logger.info( 'Shutdown complete.' )

        sys.exit(0)

    def joystick_control(self):
        for event in self.gamepad.read_loop():
            decoded_event = self.decode_event( event )
            if decoded_event['type'] == 'BUTTON' or decoded_event['type'] == 'AXIS':
                publisher = self.publishers.get(decoded_event['name'], None)
                if publisher:
                    publisher.set( decoded_event['value'] )

    def set_lidar_state(self,new_state):
        curr_state = self.lidar_state

        if curr_state != new_state:
            logger.debug( 'State Transition From %s to %s' % (curr_state.name, new_state.name) )
            if new_state == LidarStates.ACQUIRING:
                self.set_bling('Pattern=Scanner,Color=RED,Speed=MEDIUM')
            elif new_state == LidarStates.ACQUIRED:
                if self.follow_distance != 0:
                    self.lidar.cancel()
                self.set_bling('Pattern=Solid,Color=GREEN')
            elif new_state == LidarStates.STOPPED:
                self.set_bling('Pattern=Solid,Color=GREEN')
            elif new_state == LidarStates.FOLLOWING:
                self.set_bling('Pattern=Blinking,Color=GREEN,Speed=MEDIUM')
            elif new_state == LidarStates.TERMINATING:
                self.set_bling('Pattern=Blinking,Color=YELLOW,Speed=MEDIUM,Segment=ALL')
            elif new_state == LidarStates.TERMINATED:
                self.set_bling('Pattern=OFF')

        self.lidar_state = new_state

    def set_bling( self, cmd_string ):
        if self.bling:
            self.bling.process_cmd(cmd_string)

    def lidar_align(self, scan_data, precision_factor=1.0):
        #
        # in order to align the robot to the closest object, we will use the 'RightJoystickX' controller
        # to turn the robot left or right until the closest object is centered in the capture zone
        #
        publisher = self.publishers.get('RightJoystickX', None)

        turning_speed = 0.0
        if scan_data.get('valid', False)==True:
            self.turning_noupdates = 0
            if publisher:
                angle = scan_data['angle']
                if angle < 5 or angle > 355:
                    turning_speed = 0.0

                    # if the lidar is acquiring the target, then
                    # transition to the acquired state and wait 
                    # for further command
                    if self.lidar_state == LidarStates.ACQUIRING:
                        self.set_lidar_state( LidarStates.ACQUIRED )
                        
                elif angle < 20 or angle > 340:
                    turning_speed = 0.2
                elif angle < 90 or angle > 270:
                    turning_speed = 0.4
                else:
                    turning_speed = 0.6
                
                # if the angle is greater than 180, then we will turn to the left
                if angle > 180:
                    turning_speed *= -1.0

                if self.lidar_state == LidarStates.FOLLOWING:
                    turning_speed *= precision_factor

            if turning_speed != self.curr_turning_speed:
                self.curr_turning_speed = turning_speed
                publisher.set( turning_speed )
                #logger.debug( 'Setting turning speed to %0.1f' % turning_speed )
        else:
            self.turning_noupdates += 1

        if self.turning_noupdates == 5:
            if self.curr_turning_speed != 0.0:
                self.curr_turning_speed = 0.0
                publisher.set( 0.0 )
                logger.debug( 'No turning updates received recently, halting robot' )


    #
    # This function will instruct the robot to follow the closest object in the capture zone, maintaining 
    # alignment on that closest object and a minimum distance from the object.
    #
    def lidar_follow(self, scan_data):

        self.lidar.print_scan_data( scan_data )

        self.lidar_align( scan_data, precision_factor=0.3 )

        publisher = self.publishers.get('LeftJoystickY', None)

        moving_speed = 0.0
        if scan_data.get('valid', False)==True:
            self.moving_noupdates = 0
            if publisher:
                distance = scan_data['distance']
                angle = scan_data['angle']
                if distance <= self.follow_distance: 
                    moving_speed = 0.0
                    self.set_lidar_state( LidarStates.STOPPED )
                elif distance < self.follow_distance + 6:
                    self.set_lidar_state( LidarStates.FOLLOWING )
                elif distance < self.follow_distance + 12:
                    moving_speed = 0.2
                elif distance < self.follow_distance + 36:
                    moving_speed = 0.3
                elif distance < self.follow_distance + 48:
                    moving_speed = 0.4
                else:
                    moving_speed = 0.6
                
                moving_speed *= -1.0

                if moving_speed != self.curr_moving_speed:
                    self.curr_moving_speed = moving_speed
                    publisher.set( moving_speed )
                    #logger.debug( 'Setting moving speed to %0.1f' % moving_speed )
                    logger.debug( 'Distance To Target: %d, Angle: %d' % (int(distance),int(angle)) )
        else:
            self.moving_noupdates += 1

        if self.moving_noupdates >= 5:
            if self.curr_moving_speed != 0.0:
                self.curr_moving_speed = 0.0
                publisher.set( 0.0 )
                logger.debug( 'No moving updates received recently, halting robot' )

    #
    # Send commands to halt any movememnt of the robot
    #
    def lidar_halt(self):
        self.publishers.get('LeftJoystickY', None).set(0.0)
        self.publishers.get('RightJoystickX', None).set(0.0)


    def lidar_control(self, port='/dev/ttyUSB0', capture_distance=48, capture_zone='0-45,315-359', follow_distance=0):
        if self.lidar == None:
            self.lidar = Lidar(port)

        self.capture_distance = capture_distance
        self.follow_distance = follow_distance
        self.lidar.build_ranges(capture_zone)

        self.set_lidar_state( LidarStates.ACQUIRING )
        self.lidar.closest_in_range(ranges=None, min_distance=capture_distance, sample_interval=0.05, callback=self.lidar_align)

        if self.follow_distance != 0:
            self.set_lidar_state( LidarStates.STOPPED )
            self.lidar.closest_in_range(ranges=None, min_distance=self.lidar.MAX_DISTANCE, sample_interval=0.05, callback=self.lidar_follow)

        self.lidar_halt()
        self.set_lidar_state( LidarStates.TERMINATING )

if __name__ == '__main__':

    #
    # parse out the command arguments
    #
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true', dest='debug', default=False)
    options = parser.parse_args()

    #
    # Read the config file
    config = read_config( filename='config.json' )

    if options.debug or config.get('debug',False) == True:
        logger.setLevel(logging.DEBUG)

    controller = FrcController(team_number=config.get('team', 9999))

    try:
        bling_config = config.get('bling', None)
        if bling_config != None:
            controller.bling = Bling( num_leds=bling_config.get('leds',12),
                                      num_segments=bling_config.get('segments',1),
                                      brightness=bling_config.get('brightness',100) )

        if config['controller'] == 'joystick':
            controller.joystick_control()
        elif config['controller'] == 'lidar':
            lidar_config = config.get('lidar',None)
            if lidar_config:
                controller.lidar_control( port=lidar_config.get('port', '/dev/ttyUSB0'),
                                          capture_zone=lidar_config.get('capture_zone', '0-60,300-359'),
                                          capture_distance=lidar_config.get('capture_distance', 30),
                                          follow_distance=lidar_config.get('follow_distance', 48) )
        else:
            logger.error( 'ERROR: No Controller Type Specified' )
            sys.exit(1)

    except KeyboardInterrupt:
        controller.shutdown();

