#CompE DP1 prototype by Clovis Tessier and Patrick Cullen

import spidev
import time
import sys
import neopixel
import board
import wiringpi


#ADC Channel list:
# channel | Input
#=================
#       0 | MIC
#       1 | AUX L
#       2 | AUX R
#       3 | AUX MONO

#function to read SPI data from mcp3004
def ReadChannel(channel):
    adc = spi.xfer2([1,(8+channel)<<4, 0])
    data = ((adc[1]&3) << 8) + adc[2]
    return data

#function to set color of pixels based on row height
def ColorPicker(row_num, state):
    if (not state):
        return (0, 0, 0)
    elif (row_num <= 4):
        return (0, 255, 0)
    elif (row_num >= 5 and row_num <= 7):
        return (255, 128, 0)
    else: #row_num = 8 or 9
        return(255, 0, 0)

#Neopixels are physically soldered into a Zig-Zag pattern to minimize wiring,
#but this messes up addressing on neopixel software object.
    
#This function takes a 2D array of tuples, which is easier to visualize, and flips rows needed to
#produce desired output on Zig-Zagged neopixel panel, returning a 1D array to be outputted
def ZigZag(input_arr):
    output_arr = [(0,0,0) for i in range(100)]

    for y in range(10):
        for x in range(10):
            if( y % 2 == 0):# Even rows need to be flipped horizontally
                output_arr[(10*y) + x] = input_arr[9-x][y]
            else: #Odd rows can be mapped as is
                output_arr[(10*y) + x] = input_arr[x][y]
    return output_arr



#Visualizes left and right channel magnitudes on
#respective halves of neopixel matrix
def StereoLevelVisualizer():
    #Calculate pk-pk magnitude of each channel
    l_mag = 2*abs(512 - ReadChannel(adc_ch_L))
    r_mag = 2*abs(512 - ReadChannel(adc_ch_R))

    #These comparison values are compared against
    #the row of the pixel
    l_comp = int((l_mag/1024) * 10)
    r_comp = int((r_mag/1024) * 10)

    #produce image
    for y in range(10):
        for x in range(5): #left half
            if(y <= l_comp):
                image[x][y] = ColorPicker(y, 1)
            else:
                image[x][y] = ColorPicker(y, 0)
        for x in range(5,10): #right half
            if(y <= r_comp):
                image[x][y] = ColorPicker(y, 1)
            else:
                image[x][y] = ColorPicker(y, 0)

    #flip image
    output = ZigZag(image)

    #map to neopixel strip and update
    for i in range(100):
        pixels[i] = output[i]

    pixels.show()


#Visualizes MONO AUX or MIC channel magnitude on neopixel matrix
def MonoLevelVisualizer():
    ch_mag = 2*abs(512 - ReadChannel(adc_ch))
    ch_comp = int((ch_mag/1024) * 10)

    for x in range(10):
        for y in range(10):
            if(y <= ch_comp):
                image[x][y] = ColorPicker(y, 1)
            else:
                image[x][y] = ColorPicker(y, 0)

    output = ZigZag(image)

    for i in range(100):
        pixels[i] = output[i]
        
    pixels.show()




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
if(str(sys.argv[1]) == 'stereo'):
    isStereo = True
    wiringpi.digitalWrite(S0_pin, 0) #Select Stereo MUX output
    wiringpi.digitalWrite(E_pin, 0) #Enable MUX output
    adc_ch_L = 1
    adc_ch_R = 2
    
elif(str(sys.argv[1]) == 'mono'):
    isStereo = False
    wiringpi.digitalWrite(S0_pin, 1) #Select Mono MUX output
    wiringpi.digitalWrite(E_pin, 0) #Enable MUX output
    adc_ch = 3

elif(str(sys.argv[1]) == 'mic'):
    isStereo = False
    wiringpi.digitalWrite(E_pin, 1) #Disable MUX output
    adc_ch = 0

else:
    sys.exit(input_err_msg)

    
#configure SPI bus channel 0
spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz=1000000

#Configure NeoPixel Strip
pixel_pin = board.D18
num_pixels = 100
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.2, auto_write = False, pixel_order=ORDER)

image = [[(0, 0, 0) for x in range(10)] for y in range(10)]

try:
    while True:
        if (isStereo):
            StereoLevelVisualizer()
        else: #MONO AUX or MIX input
            MonoLevelVisualizer()

        time.sleep(1/30)
            

except KeyboardInterrupt:
	pixels.deinit()
	wiringpi.digitalWrite(E_pin, 1) #disable MUX output
	sys.exit()


