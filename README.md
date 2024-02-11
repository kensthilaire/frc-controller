# frc-controller
Python application to control FRC robot using network tables.

The controller application communicates "joystick" instructions to the FRC robot to control the movement.

The controller application supports a RP LIDAR to create a "follow me" robot that will find the closest object in its capture zone and follow that closest object as it moves across a space. If another object moves closer to the robot than the one being followed, the robot will change course and now follow the now-closest object.

A LED strip application (aka "bling") is used to convey the current state of the application as the LIDAR senses and follows.

This application has been tested on a Raspberry Pi-3 and with a Slamtec A2M8 LIDAR device. The LED strip used in this application is a strip of LPD8806 LEDs.
