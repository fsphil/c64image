#!/usr/bin/python3

# c64image.py
#
# A small python program to convert an image to Commodore 64 multi-colour
# bitmap data. Output can be an executable PRG or a header file.
#
# - Philip Heron <phil@sanslogic.co.uk>
#
# --
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# --

import sys
import math
import random
import argparse
from PIL import Image

p = argparse.ArgumentParser(description = 'Convert an image to a Commodore 64 multi-colour bitmap.')
p.add_argument('input', help='The image file to read.')
p.add_argument('output', help='Output filename.')
p.add_argument('-f', '--format', help='Set the output file format S, H, or PRG. Default: S', default = 'S')
p.add_argument('-b', '--background', help='Set the background colour 0-15. Default: Auto', default = False, type=int)
p.add_argument('--id', help='Set the image ID in S or H files', default = 'image')
args = p.parse_args()

background = args.background
out_format = args.format.upper()
image_id = args.id

if background != False and (background < 0 or background > 15):
    p.print_usage()
    print("Invalid background colour " + str(background))
    exit()

if out_format not in ('S', 'H', 'PRG'):
    p.print_usage()
    print("Invalid output format " + out_format)
    exit()

# Open and convert the image to 160x200 RGB frame
im = Image.open(args.input).convert('RGB').resize((160, 200), Image.BICUBIC)

# The C64 palette
palette = (
    (0x00, 0x00, 0x00),
    (0xFF, 0xFF, 0xFF),
    (0x88, 0x00, 0x00),
    (0xAA, 0xFF, 0xEE),
    (0xCC, 0x44, 0xCC),
    (0x00, 0xCC, 0x55),
    (0x00, 0x00, 0xAA),
    (0xEE, 0xEE, 0x77),
    (0xDD, 0x88, 0x55),
    (0x66, 0x44, 0x00),
    (0xFF, 0x77, 0x77),
    (0x33, 0x33, 0x33),
    (0x77, 0x77, 0x77),
    (0xAA, 0xFF, 0x66),
    (0x00, 0x88, 0xFF),
    (0xBB, 0xBB, 0xBB),
)

palette_names = (
    'Black',
    'White',
    'Red',
    'Cyan',
    'Violet',
    'Green',
    'Blue',
    'Yellow',
    'Orange',
    'Brown',
    'Lightred',
    'Dark Grey',
    'Medium Grey',
    'Light Green',
    'Light Blue',
    'Light Grey',
)

# Colour usage counters, palette order
ccounter = [0] * 16

# Create the canvas. This represents an 'ideal' C64 image where
# there are no colour restrictions within the blocks
canvas = [[[[0] * 4 for row in range(8)] for ccol in range(40)] for crow in range(25)]

# Convert an (r, g, b) value to the nearest C64 palette entry
def rgb2pal(colour):
    
    s = -1
    c = -1
    
    # Random noise dither
    #colour = list(colour)
    #colour[0] += random.randint(-32,32)
    #colour[1] += random.randint(-32,32)
    #colour[2] += random.randint(-32,32)
    
    for x in range(0, len(palette)):
        d = abs(math.sqrt(
            (colour[0] - palette[x][0]) ** 2 +
            (colour[1] - palette[x][1]) ** 2 +
            (colour[2] - palette[x][2]) ** 2
        ))
        
        if s == -1 or d < s:
            s = d
            c = x
    
    return c

# Find the nearest C64 palette entry from a list of palette codes
def pal2pal(colour, colours):
    
    s = -1
    c = -1
    
    colour = palette[colour]
    
    for x in range(0, len(colours)):
        d = abs(math.sqrt(
            (colour[0] - palette[colours[x]][0]) ** 2 +
            (colour[1] - palette[colours[x]][1]) ** 2 +
            (colour[2] - palette[colours[x]][2]) ** 2
        ))
        
        if s == -1 or d < s:
            s = d
            c = colours[x]
    
    return c

# Write bytes to a string
def write_bytes(name, data, cformat):
    
    if cformat == 'S':
        s = "%s\n" % name
        
        for line in (data[x:x + 32] for x in range(0, len(data), 32)):
            s += "\t.byte " + ",".join(("$%02X" % x for x in line)) + "\n"
    
    elif cformat == 'H':
        s = "unsigned char %s[0x%d] = [\n" % (name, len(data))
        
        for line in (data[x:x + 32] for x in range(0, len(data), 32)):
            s += "\t" + ",".join(("0x%02X" % x for x in line)) + ",\n"
        
        s += "];\n";
    
    return s

# Render the PIL image to the canvas
for cy in range(0, 25):
    for cx in range(0, 40):
        
        ox = cx * 4
        oy = cy * 8
        
        for y in range(0, 8):
            for x in range(0, 4):
                
                p = rgb2pal(im.getpixel((ox + x, oy + y)))
                canvas[cy][cx][y][x] = p
                ccounter[p] += 1

if background == False:
    
    # Select the background based on the most used colour
    background = ccounter.index(max(ccounter))
    print("Using %s (%d) for background colour" % (palette_names[background], background))

else:
    
    print("Background fixed at %s (%d)" % (palette_names[background], background))

# Initialise the bitmap buffer
bitmap_bytes = []
screen_bytes = []
colour_bytes = []

last_colours = False

for cy in range(0, 25):
    for cx in range(0, 40):
        
        # Make a list of all the colours used in this block
        # Background is always used, even if not referenced
        colours = [background]
        ccounter = [0]
        
        for row in canvas[cy][cx]:
            for colour in row:
                
                if not colour in colours:
                    colours.append(colour)
                    ccounter.append(0)
                
                ccounter[colours.index(colour)] += 1
        
        # Sort the colours, background first then most used to least
        colours = [background] + list(x[1] for x in sorted(zip(ccounter[1:], colours[1:]), reverse = True))
        
        if len(colours) > 4:
            print("Block %dx%d has too many non-background colours: %s -> %s" % (cx, cy, colours[1:], colours[1:4]))
            
            # Crop colour list to the background and 3 most used values
            colours = colours[:4]
            
            # Replace removed colours in the block with the nearest valid match
            for y in range(8):
                for x in range(4):
                    
                    p = canvas[cy][cx][y][x]
                    
                    if not p in colours:
                        canvas[cy][cx][y][x] = pal2pal(p, colours)
        
        # If all the colours of this block are present in the previous block,
        # use that same order. This may help with RLE compression.
        if last_colours != False and set(colours).issubset(set(last_colours)):
            colours = last_colours
        
        elif len(colours) != 4:
            colours += [0] * (4 - len(colours))
        
        last_colours = colours
        
        # Output this block
        for row in canvas[cy][cx]:
            bitmap_bytes.append(colours.index(row[0]) << 6 | colours.index(row[1]) << 4 | colours.index(row[2]) << 2 | colours.index(row[3]))
        
        screen_bytes.append(colours[1] << 4 | colours[2])
        colour_bytes.append(colours[3])

# Write the results
if out_format == 'S':
    s  = "\n%s_background = %d\n\n" % (image_id, background)
    s += write_bytes(image_id, bitmap_bytes, out_format) + "\n"
    s += write_bytes(image_id + "_screen", screen_bytes, out_format) + "\n"
    s += write_bytes(image_id + "_colour", colour_bytes, out_format) + "\n"
    s = bytes(s, encoding='utf-8')

elif out_format == 'H':
    s  = "\n#define %s_background %d\n\n" % (image_id, background)
    s += write_bytes(image_id, bitmap_bytes, out_format) + "\n"
    s += write_bytes(image_id + "_screen", screen_bytes, out_format) + "\n"
    s += write_bytes(image_id + "_colour", colour_bytes, out_format) + "\n"
    s = bytes(s, encoding='utf-8')

elif out_format == 'PRG':
    # This string is the binary produced from the assembly program "showimg.s"
    # Pay no attention to the ugly hack to set the background colour.
    s = bytes.fromhex(
        ('01080c080d089e3230363100000078a240a01f205608a9008d6308a9448d6408a2e' +
        '8a003205608a9008d6308a9d88d6408a2e8a003205608a91c8d18d0a93b8d11d0a9' +
        '188d16d0a9028d00dda9%02X8d20d08d21d04c5308e8c8cad00488d00160ad78088d0' +
        '060ee6008d003ee6108ee6308d003ee64084c5808') % background
    )
    s += bytes(bitmap_bytes) + bytes(screen_bytes) + bytes(colour_bytes)

open(args.output, 'wb').write(s)

