import sys
import neopixel
import board
from PIL import Image

#Neopixels rows are commonly soldered end to end  into a Zig-Zag pattern to minimize wiring,
#but this can make addressing of individual pixels more complicated

#This function is an output driver for our neopixel panel, it takes a 1 or 2 dimensional list  as input,
#flips the necessary rows to generate proper output, and returns a 1 dimensional list that can be directly
#copied to the neopixel object.
#optional arg origin is used to specify (in cartesian coordinates) where the 0th pixel of input_arr should be assigned.
#    (0,0) = bottom left corner
#    (0,1) = top left corner
#    (1,0) = bottom right corner
#    (1,1) = top right corner

#For the particular panel we are using, the first pixel is physically in the bottom right corner.
def ZigZag(input_lst, is1D = True, origin = (0,1) ):
    output_lst = [(0,0,0) for i in range(100)]
    im = Image.new(mode='RGB', size=(10,10))

    if (is1D):
        input_lst_cp = input_lst
    else: #2D array input
        input_lst_cp = [input_lst[x][y] for x in range(10) for y in range(10)]

    #Load into Image object to flip image into correct orientation
    im.putdata(input_lst_cp)

    if(origin[0] == 1):
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if(origin[1] == 1):
        im = im.transpose(Image.FLIP_TOP_BOTTOM)

    im_data = list(im.getdata())

    for y in range(10):
        for x in range(10):
            if( y % 2 == 0): #Even rows need to be flipped horizontally
                output_lst[(10*y) + x] = im_data[(10*y) + (9-x)]
            else: #Odd rows can be mapped as is
                output_lst[(10*y) + x] = im_data[(10*y) + x]
    return output_lst

#Like ZigZag but for 1-Dimensional array of tuples
def ZigZag1D(input_arr):
    output_arr = [(0,0,0) for i in range(100)]

    for y in range(10):
        for x in range(10):
            if( y % 2 == 0):# Even rows need to be flipped horizontally
                output_arr[(10*y) + x] = input_arr[(10*y) + (9-x)]
            else: #Odd rows can be mapped as is
                output_arr[(10*y) + x] = input_arr[(10*y) + x]
    return output_arr


#Configure NeoPixel Strip
pixel_pin = board.D18
num_pixels = 100
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=1.0, auto_write = False, pixel_order=ORDER)

im = Image.open(sys.argv[1]) #open the image
im = im.convert("RGB")
im = im.resize((10,10))

im_data = list(im.getdata())
output_data = ZigZag(im_data)

for i in range(num_pixels):
	pixels[i] = output_data[i]

pixels.show()

