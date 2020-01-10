import sys
import neopixel
import board
import spidev
import time
import wiringpi
import queue
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

def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos*3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos*3)
        g = 0
        b = int(pos*3)
    else:
        pos -= 170
        r = 0
        g = int(pos*3)
        b = int(255 - pos*3)
    return (r, g, b) if ORDER == neopixel.RGB or ORDER == neopixel.GRB else (r, g, b, 0)


#ADC Channel list:
# channel | Input
#=================
#       0 | MIC
#       2 | AUX L
#       1 | AUX R
#       3 | AUX MONO

#function to read SPI data from mcp3004
def ReadChannel(channel):
    adc = spi.xfer2([1,(8+channel)<<4, 0])
    data = ((adc[1]&3) << 8) + adc[2]
    return data

def ShiftImage(shift_color):
    for i in range(len(IM_DATA_ORIG)):
        curr_pixel = IM_DATA_ORIG[i]
        curr_pixel_r = (curr_pixel[0] + shift_color[0]) % 256
        curr_pixel_g = (curr_pixel[1] + shift_color[1]) % 256
        curr_pixel_b = (curr_pixel[2] + shift_color[2]) % 256
        im_data_new[i] = (curr_pixel_r, curr_pixel_g, curr_pixel_b)
    return im_data_new

    #MUX Channel List:
# S0 | Input
#=================
#  0 | Stereo
#  1 | Mono

#MUX control pins
S0_pin = 5
E_pin = 6 #Output Enable (active LOW)

#Configure pins as OUTPUT
wiringpi.wiringPiSetupGpio()
wiringpi.pinMode(S0_pin, 1) #S0
wiringpi.pinMode(E_pin, 1) #E


input_err_msg = 'No input selected! Try running again, this time passing one of the following\ninput arguments:\nstereo\nmono\nmic\n'
#Determine input selection from cmd line argument, return error if no valid input selected
#Valid input:
#stereo
#mono
#mic

    
elif(str(sys.argv[1]) == 'mono' or str(sys.argv[1]) == 'stereo'):
    wiringpi.digitalWrite(S0_pin, 1) #Select Mono MUX output
    wiringpi.digitalWrite(E_pin, 0) #Enable MUX output
    adc_ch = 3

elif(str(sys.argv[1]) == 'mic'):
    wiringpi.digitalWrite(E_pin, 1) #Disable MUX output
    adc_ch = 0

else:
    sys.exit(input_err_msg)


#Configure NeoPixel Strip
pixel_pin = board.D18
num_pixels = 100
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.5, auto_write = False, pixel_order=ORDER)

im = Image.open(sys.argv[2]) #open the image
im = im.convert("RGB")
im = im.resize((10,10))

IM_DATA_ORIG = list(im.getdata())


image = [[(0, 0, 0) for x in range(10)] for y in range(10)]

NUM_SAMPLES = 100
samples = queue.Queue(NUM_SAMPLES)




try:
    while (samples.full() == False):
        curr_sample = int(abs(ReadChannel(adc_ch) - 512) % 256)
        samples.put(curr_sample)
    while True:
        #read ADC data
        curr_avg = 0
        for sample in list(samples):
            curr_avg = curr_avg + sample
        curr_avg = int(curr_avg / NUM_SAMPLES)


        #determine color to shift
        curr_color = wheel(curr_avg)
        shift_r = int(curr_color[0] / 25)
        shift_g = int(curr_color[1] / 25)
        shift_b = int(curr_color[2] / 25)
        shift_color = (shift_r, shift_g, shift_b)
        #shift image
        im_data = ShiftImage(shift_color)
        #output image
        output_data = ZigZag(im_data)
        for i in range(num_pixels):
        pixels[i] = output_data[i]
        pixels.show()

        samples.get()
        samples.put()
        


            

except KeyboardInterrupt:
    pixels.deinit()
    wiringpi.digitalWrite(E_pin, 1) #disable MUX output
    sys.exit()




pixels.show()