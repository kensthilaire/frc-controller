'''
Created on Feb 5, 2017

@author: ksthilaire
'''

import bibliopixel.colors as colors

#
# This is the set of color maps for the Bling. Each color map is made up of one or more
# colors as defined in the BiblioPixel color module. For solid colors, provide just one
# color in the list, but for complex color maps, provide as many colors as you want
#
color_map = {
    'RED': [ colors.Red ],
    'GREEN': [ colors.Green ],
    'YELLOW': [ colors.Yellow ],
    'BLUE': [ colors.Blue ],
    'MIDNIGHTBLUE': [ colors.MidnightBlue ],
    'TEAL': [ colors.Teal ],
    'INDIANRED': [ colors.IndianRed ],
    'SALMON': [ colors.Salmon ],
    'PLAID': [ colors.Plaid ],
    'LIGHTPINK': [ colors.LightPink ],
    'GOLD': [ colors.Gold ],
    'SIENNA': [ colors.Sienna ],
    'LIME': [ colors.Lime ],
    'INDIGO': [ colors.Indigo ],
    'DARKVIOLET': [ colors.DarkViolet ],
    'DEEPPINK': [ colors.DeepPink ],
    'AMETHYST': [ colors.Amethyst ],
    'MINT': [ colors.MintCream ],
    'HOTPINK': [ colors.HotPink ],
    'PINK': [ colors.Pink ],
    'PURPLE': [ colors.Purple ],
    'PLUM': [ colors.Plum ],
    'AQUA': [ colors.Aqua ],
    'BLACK': [ colors.Black ],
    'VIOLET': [ colors.Violet ],
    'NAVY': [ colors.Navy ],
    'SKY': [ colors.SkyBlue ],
    'DARKGREEN': [ colors.ForestGreen ],
    'SEAGREEN': [ colors.SeaGreen ],
    'MAROON': [ colors.Maroon ],
    'ORCHID': [ colors.Orchid ],
    'CORAL': [ colors.Coral ],
    'OLD': [ colors.OldLace ],
    'LEMON': [ colors.LemonChiffon ],
    'ORANGE': [ colors.Orange ],
    'LIGHTGREEN': [ colors.YellowGreen ],
    'BLACKANDYELLOW': [ colors.Black, colors.Yellow ],
    'PINKY': [ colors.Pink, colors.HotPink, colors.Salmon, colors.LightPink, colors.DeepPink, colors.Coral],
    'TEAMCOLORS' : [ colors.Blue, colors.Orange ],
    'RAINBOW': [colors.Red, colors.Orange, colors.Yellow, colors.Green, colors.Blue, colors.Purple],
    'CHRISTMAS': [colors.Red, colors.Green],
    'BROWN': [colors.Blue, colors.Orange, colors.Purple],

    # insert all color maps above this line to keep the error colors last    
    'ERROR': [colors.Red,]
    
    }

#
# Function to get the list of colors that map to the color string.
# This function is used by those animations that require a list of colors to display (like RAINBOW)
#
# If the specified color string does not map to any colors, then the ERROR color list is returned to 
# make it obvious that the color string is unknown.
#
def get_colors( color_str ):
    color_str = color_str.upper()
    try:
        colors = color_map[color_str]
    except:
        colors = color_map['ERROR']
    return colors

#
# Function to get the first color from the list of colors that map to the color string.
# This function is used by those animations that require only one color instead of a list of colors
#
# If the specified color string does not map to any colors, then the first color from the ERROR color 
# list is returned to make it obvious that the color string is unknown.
#
def get_first_color( color_str ):
    color_str = color_str.upper()
    try:
        colors = color_map[color_str][0]
    except:
        colors = color_map['ERROR'][0]
    return colors
    
if __name__ == '__main__':
    pass
    
