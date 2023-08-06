import sys
from bling import Bling
from optparse import OptionParser

def bling_menu( bling ):
    print( bling.menu() )

    done = False
    while not done:
        try:
            selection = input('Enter your selection: ')
            if selection == '?':
                print( bling.menu() )
            elif selection == '':
                bling.stop_animation()
            elif selection.lower() == 'q':
                done = True
            elif selection.lower() == 'b':
                brightness = input('Enter brightness level(0-255): ')
                level = int(brightness)
                try:
                    bling.set_brightness(level)
                except ValueError:
                    print( 'Invalid brightness level' )
            else:
                try:
                    result = bling.menu_select(int(selection))
                    print( result )
                except ValueError:
                    print( 'Invalid input choose a number: %s' % selection )

        except KeyboardInterrupt:
            done = True

    print( '\nDone!' )

# command line options handling
parser = OptionParser()

parser.add_option(
    "-l","--leds",dest="leds", default='48',
    help='Total number of LEDs in the strip')
parser.add_option(
    "-s","--segments",dest="segments", default=None,
    help='Number of LED segments in the strip')
parser.add_option(
    "-b","--brightness",dest="brightness", default='255',
    help='Overall brightness of the LEDs from 0-255, with 255 being the brightest')


# Parse the command line arguments
(options,args) = parser.parse_args()

if options.segments is not None:
    num_segments = int(options.segments)
else:
    num_segments = None

try:
    bling = Bling(int(options.leds), num_segments, int(options.brightness))
except ValueError:
    sys.exit('ERROR: Invalid Brightness Level: %s, must be 0-255' % options.brightness)

bling_menu( bling )

