
from bibliopixel import Strip

#
# The current implementation supports the LPD8806 LED strips using the SPI device.
# Other LED strip types and interfaces may be added over time.
#
from bibliopixel.drivers.SPI.LPD8806 import *
from bibliopixel.drivers.spi_interfaces import SPI_INTERFACES

import bling_patterns

class Bling(object):

    def __init__(self, num_leds, num_segments=None, brightness=127, ledtype='LPD8806', comms='SPI', dev='/dev/spidev0.0'):

        # set the total number of LEDs in the strip
        self.num_leds = num_leds
        self.num_segments = num_segments
        self.brightness = brightness
        self.dev = dev
        
        # initialize the list of segment overrides to include all, left and right.
        # This segment list is used to override other segment control based on
        # the bling command itself. For example, we may want to apply a pattern to either
        # the left or right side of the robot.
        led_half = int((self.num_leds/2))
        led_quarter = int((self.num_leds/4))
        self.segments = { 'ALL':          ( 0, self.num_leds ),
                          'LEFT':         ( 0, led_half-1 ),
                          'RIGHT':        ( led_half, int(self.num_leds) ),
                          'RIGHT_FRONT':  ( 0, (led_quarter-1) ),
                          'RIGHT_REAR':   ( led_quarter, (led_quarter+led_quarter-1) ),
                          'LEFT_REAR':    ( (led_quarter*2), ((led_quarter*2)+led_quarter-1) ),
                          'LEFT_FRONT':   ( (led_quarter*3), ((led_quarter*3)+led_quarter-1) )
                        }

        # initialize the driver with the type and count of LEDs that we are using
        # also, define the correct RGB channel order once you have run the test pattern
        # the other parameters are set based on the controlling application. 
        # We're using the RaspberryPi as the controller with the SPI port
        if ledtype == 'LPD8806':
            if comms == 'SPI':
                self.driver = LPD8806(num=self.num_leds, c_order = ChannelOrder.GRB, spi_speed=2, spi_interface=SPI_INTERFACES.PYDEV, dev=self.dev)
            else:
                self.driver = None
                raise Exception( 'Sorry, only communication using the SPI interface is supported at this time' )
        else:
            self.driver = None
            raise Exception( 'Sorry, only LPD8806 LED strips are supported at this time' )

        # we are using the LED strip configuration, other available configurations include an LED matrix,
        # but we have only a single strip at this time
        self.layout = Strip(self.driver, threadedUpdate=True, brightness=self.brightness)

        # the frames per second is used to control how fast the animation runs. some of the animations
        # work better when run at a low frames per second
        self.fps = None

        # the pattern variable contains the most recent bling pattern that has been assigned
        self.pattern = None
        
        # initialize the bling command parameters to provide reasonable default values for each
        # setting
        self.params = {}
        self.init_params()
        
        self.bling_patterns = bling_patterns.BlingPatterns(self)

        ###### TODO: remove these variables after converting the menu processing to use #####
        ######       the new patterns                                                   #####
        # animation object containing pattern to apply to the LEDs
        self.anim = None

        # flag to indicate whether the selected mode requires animation. Displaying a solid color across all or a range
        # of LEDs does not require animation
        self.animate = True

    def get_num_leds(self):
        return self.num_leds

    def get_num_segments(self):
        return self.num_segments

    def get_segment_size(self):
        return int(self.num_leds/self.num_segments)

    def get_segment_min_max_led( self, num_segments, segment_index ):
        segment_leds = int(self.num_leds/num_segments)
        min_led = segment_leds*segment_index
        max_led = min_led+segment_leds-1
        return min_led,max_led
        
    def set_brightness(self, level):
        self.layout.set_brightness(level)
        self.brightness = level

    def stop_animation(self):
        # reset the brightness level back to the default value that was set upon initialization
        self.layout.set_brightness(self.brightness)

        if self.pattern is not None:
            self.pattern.stop()
        else:
            if self.anim is not None:
                self.anim.join()
                self.anim.stop()
            self.layout.all_off()
            self.layout.update()

    def get_leds_from_segment(self, segment_str):
        segment_leds = [0,-1]
        try:
            segment_def = self.segments[segment_str]
            segment_leds[0] = segment_def[0]
            segment_leds[1] = segment_def[1]
        except:
            # if the specified segment doesn't exist, return all LEDs
            pass
            segment_leds = [0,-1]
        return segment_leds

    def init_params(self):
        self.params['Pattern'] = 'Error'
        self.params['Segment'] = 'All'
        self.params['Color'] = 'Error'
        self.params['Speed'] = 'Medium'
        self.params['Min'] = '0'
        self.params['Max'] = '100'
        self.params['Brightness'] = str(self.brightness)

    def apply_min_max_params(self, leds):
        # Re-calculate the minimum and maximum LED values by applying any
        # specified min/max percentage parameter setting
        min_param = int(self.params['Min'])
        max_param = int(self.params['Max'])
        if min_param > 100:
            print( 'Invalid  Minimum Setting: %d, Must be 0-100' % min_param )
            min_param = 0
        if max_param > 100:
            print( 'Invalid  Maximum Setting: %d, Must be 0-100' % max_param )
            max_param = 100
        led_range = leds[1]-leds[0]
        min_adjust=0
        max_adjust=0
        if min_param != 0:
            min_adjust = int((float(led_range)*(min_param)/100)+1)
            #min_adjust = int(float((min_param/led_range)*100))
            leds[0] += min_adjust
        if max_param != 100:
            max_adjust = int((float(led_range)*(100-max_param)/100)+1)
            leds[1] -= max_adjust
        return leds
    
    def process_cmd(self, cmd_str):
        result = 'OK'

        # start by starting any animation that is already running
        self.stop_animation()

        # re-initialize the animation parameters to the default settings
        self.init_params()
        
        try:
            # Parse command string into parameter list
            print( 'Command: %s' % cmd_str )
            cmd_params=cmd_str.split(',')
            for param in cmd_params:
                name,value=param.split('=')
                self.params[name.title()] = value.upper()
    
            if self.params['Pattern'] == 'OFF':
                # if the patter is OFF, then simply return. we have already turned off
                # the LEDs
                return result

            # process the command based on the provided parameters
            # first get the specified pattern
            self.pattern = self.bling_patterns.get_pattern(self.params['Pattern'].upper())
            
            # process the segment parameter, getting the list of LEDs that will be
            # controlled by this command
            leds = self.get_leds_from_segment( self.params['Segment'])
            leds = self.apply_min_max_params( leds )

            # if the pattern specifies a brightness level, then update the level for the entire strip
            try:
                brightness = int(self.params['Brightness'])
                self.layout.set_brightness(brightness)
            except ValueError:
                print( 'Invalid Brightness Value: %d' % brightness )
            except KeyError:
                pass

            self.pattern.setup( self.layout, self.params['Color'], self.params['Speed'], leds[0], leds[1], self.num_segments )

            # run the configured pattern
            self.pattern.run()
    
        except:
            raise
            # catch any thrown exceptions and generate the error pattern
            print( 'Error processing command: %s' % cmd_str )
            self.pattern = self.bling_patterns.get_pattern('Error')
            self.pattern.setup(self.layout, 'RED')
            self.pattern.run()

            result = 'ERROR'

        return result

 
    # TODO: Most of the following code will be removed once we complete the implementation of the pattern
    # classes and convert the menu over to using the pattern classes insead
    def menu(self):
        menu_str  = '\n'
        menu_str += '                              Available Bling Patterns\n\n'
        menu_str += '(1)  Alternates (two alternating colors)        '
        menu_str += '(14) Linear Rainbow (another variation)\n'
        menu_str += '(2)  Color Chase (one LED moving end to end)    '
        menu_str += '(15) Search Lights (colors moving up/down)\n'
        menu_str += '(3)  Color Fade (one color fading in/out)       '
        menu_str += '(16) Wave (colors moving up/down)\n'
        menu_str += '(4)  Color Pattern (mix of colors)              '
        menu_str += '(17) Solid Red (one color on all LEDs)\n'
        menu_str += '(5)  Color Wipe (one color moving up/down)      '
        menu_str += '(18) Solid Yellow (one color on all LEDs)\n'
        menu_str += '(6)  Fire Flies (colors randomly blinking)      '
        menu_str += '(19) Solid Green (one color on all LEDs)\n'
        menu_str += '(7)  Scanner (one color moving up/down)         '
        menu_str += '(20) Test Strip (test pattern for RGB cal.)\n'
        menu_str += '(8)  Rainbow Scanner (colors moving up/down)    '
        menu_str += '(21) Blinking Green (slow on all LEDs)\n'
        menu_str += '(9)  Ping Pong (colors bouncing around)         '
        menu_str += '(22) Blinking Green (medium on all LEDs)\n'
        menu_str += '(10) Party Mode (colors blinking on/off)        '
        menu_str += '(23) Blinking Green (fast on all LEDs)\n'
        menu_str += '(11) Rainbow Halves (strand divided in two      '
        menu_str += '(24) Blinking Green (medium on left LEDs)\n'
        menu_str += '(12) Rainbow (set of colors moving end to end)  '
        menu_str += '(25) Blinking Green (medium on right LEDs)\n'
        menu_str += '(13) Rainbow Cycles (variation of above)        '
        menu_str += '\n'
        menu_str += '\n'
        menu_str += '\n'
    
        return menu_str


    def menu_select( self, menu_selection ):
        result = 'OK'

        if menu_selection == 1:
            # Alternates
            result = self.process_cmd('Pattern=Alternates,Color=TEAMCOLORS,Speed=MEDIUM,Segment=ALL')
        elif menu_selection == 2:
            # Color Chase
            result = self.process_cmd('Pattern=ColorChase,Color=GREEN,Speed=MEDIUM')
        elif menu_selection == 3:
            # Color Fade
            result = self.process_cmd('Pattern=ColorFade,Color=RAINBOW,Speed=MEDIUM')
        elif menu_selection == 4:
            # Color Pattern
            result = self.process_cmd('Pattern=ColorPattern,Color=RAINBOW,Speed=MEDIUM')
        elif menu_selection == 5:
            # Color Wipe
            result = self.process_cmd('Pattern=ColorWipe,Color=GREEN,Speed=MEDIUM')
        elif menu_selection == 6:
            # Fire Flies
            result = self.process_cmd('Pattern=FireFLies,Color=RAINBOW,Speed=MEDIUM')
        elif menu_selection == 7:
            # Scanner
            result = self.process_cmd('Pattern=Scanner,Color=BLUE,Speed=MEDIUM')
        elif menu_selection == 8:
            # Rainbow Scanner
            result = self.process_cmd('Pattern=RainbowScanner,Color=RAINBOW,Speed=MEDIUM')
        elif menu_selection == 9:
            # Ping Pong
            result = self.process_cmd('Pattern=PingPong,Color=BLUE,Speed=MEDIUM')
        elif menu_selection == 10:
            # Party Mode
            result = self.process_cmd('Pattern=PartyMode,Color=RAINBOW,Speed=MEDIUM')
        elif menu_selection == 11:
            # Rainbow Halves
            result = self.process_cmd('Pattern=RainbowHalves,Color=RAINBOW,Speed=MEDIUM')
        elif menu_selection == 12:
            # Rainbow
            result = self.process_cmd('Pattern=Rainbow,Color=RAINBOW,Speed=MEDIUM')
        elif menu_selection == 13:
            # Rainbow Cycle
            result = self.process_cmd('Pattern=RainbowCycle,Color=RAINBOW,Speed=MEDIUM')
        elif menu_selection == 14:
            # Linear Rainbow
            result = self.process_cmd('Pattern=LinearRainbow,Color=RAINBOW,Speed=MEDIUM')
        elif menu_selection == 15:
            # Search Lights
            result = self.process_cmd('Pattern=SearchLights,Color=RAINBOW,Speed=MEDIUM')
        elif menu_selection == 16:
            # Wave
            result = self.process_cmd('Pattern=Wave,Color=BLUE,Speed=MEDIUM')
        elif menu_selection == 17:
            # Solid Red
            result = self.process_cmd('Pattern=Solid,Color=RED')
        elif menu_selection == 18:
            # Solid Yellow
            result = self.process_cmd('Pattern=Solid,Color=YELLOW')
        elif menu_selection == 19:
            # Solid Green
            result = self.process_cmd('Pattern=Solid,Color=GREEN')
        elif menu_selection == 20:
            # Test Pattern
            # This animation is used to test the strip and the color order
            result = self.process_cmd('Pattern=Test,Color=TEST,Speed=MEDIUM')
        elif menu_selection == 21:
            result = self.process_cmd('Pattern=Blinking,Color=PURPLE,Speed=SLOW,Segment=ALL')
        elif menu_selection == 22:
            result = self.process_cmd('Pattern=Blinking,Color=GREEN,Speed=MEDIUM,Segment=ALL')
        elif menu_selection == 23:
            result = self.process_cmd('Pattern=Blinking,Color=GREEN,Speed=FAST,Segment=ALL')
        elif menu_selection == 24:
            result = self.process_cmd('Pattern=Blinking,Color=GREEN,Speed=MEDIUM,Segment=LEFT')
        elif menu_selection == 25:
            result = self.process_cmd('Pattern=Blinking,Color=GREEN,Speed=MEDIUM,Segment=RIGHT')
        elif menu_selection == 99:
            # All off
            result = self.process_cmd('Pattern=OFF')
        else:
            raise ValueError
            result = 'ERROR'

        return result

#
# global bling server instance used when running the bling service as a singleton
#
bling_server = None

#
# Utility function to retrieve the global bling server instance
#
def get_bling_server():
    return bling_server

#
# Utility function to create the single global instance of the bling server
#
def create_bling_server(num_leds, num_segments=None, brightness=255):
    global bling_server
    try:
        if bling_server is not None:
            sys.exit('ERROR: Bling server already created')

        bling_server = Bling(num_leds, num_segments, brightness)
    except ValueError:
        sys.exit('ERROR: Invalid Brightness Level: %s, must be 0-255' % brightness)

#
# Utility function to process a bling command string by the global bling server
#
def process_cmd(cmd_str):
    bling_server.process_cmd(cmd_str)

#
# Utility function to cancel an active bling animation sequence by the global bling server
#
def stop_animation():
    bling_server.stop_animation()

