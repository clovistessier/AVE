#script to test ability to sample and perform fft in realtime
#prints the dominant frequency of the current sampling window
import spidev
import time
import sys
import neopixel
import board
import wiringpi
import numpy as np
from collections import deque


FRAC_COLUMN_WIDTHS_MONO = [1 + 0.3*i for i in range(10)]

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



def MonoSpectrumVisualizer():
    #Sample time and ADC value from channel
    sample_tuples = [(time.time(), ReadChannel(adc_ch)) for i in range(num_samples)]

    #Separate time and sample values
    start_time = sample_tuples[0][0]
    times = [t[0]-start_time for t in sample_tuples]
    sample = [t[1] for t in sample_tuples]

    sampling_frequency = num_samples/times[-1]

    #Perform FFT
    fft = np.fft.fft(sample)
    fft = fft[:num_samples // 2] #We only care about the first half since FFT is symmetric

    # x = np.argsort(fft[:num_samples // 2])
    # dom_f = (x[0] / num_samples) * sampling_frequency
    # x_max = abs(fft[x[0]])
    # print(dom_f, x_max)

    #Generate Image:

    #Divide the FFT bandwidth (10 kHz) into 10 output bands, one for each column of the array
    #Currently they're just divided evenly, but in the future the widtch of each output band will be
    #tuned to have the most movement on the LED matrix
    column_bw = len(fft) // 10

    for x in range(10):
        #Average the magnitudes of the frequencies in each output band
        band_mag = np.mean( [ abs(fft[x*column_bw+w]) for w in range(column_bw) ] )
        if(x == 0):
            #lowest frequencies always seem to have MUCH higher magnitude than the rest, this just makes it look nicer
            #Will be tuned in the future
            band_mag -= 10000

        #This normalization value will need to be tuned as well
        mag_normalized = band_mag / 500 # normalize to value between 0 and 10 to compare against row height 

        #turn on neopixels in each respective column
        for y in range(10):
            if (y <= mag_normalized):
                image[x][y] = ColorPicker(y, 1)
            else:
                image[x][y] = ColorPicker(y, 0)


    output = ZigZag(image)

    for i in range(100):
        pixels[i] = output[i]

    pixels.show()


def StereoSpectrumVisualizer():
    #Sample time and ADC value from channel
    sample_tuples = [(time.time(), ReadChannel(adc_ch_L), ReadChannel(adc_ch_R)) for i in range(num_samples)]

    #Separate time and sample values
    start_time = sample_tuples[0][0]
    times = [t[0]-start_time for t in sample_tuples]
    sample_L = [t[1] for t in sample_tuples]
    sample_R = [t[2] for t in sample_tuples]

    sampling_frequency = num_samples/times[-1]

    #Perform FFT
    fft_L = np.fft.fft(sample_L)
    fft_L = fft_L[1:num_samples // 2] #We only care about the first half since FFT is symmetric
    
    fft_R = np.fft.fft(sample_R)
    fft_R = fft_R[1:num_samples // 2]
    

    #Generate Image:
    #AUX_L Spectrum will be on left half of the image, AUX_R Spectrum on the right half (5 columns each)
    #Spectrums will mirror each other, with lowest frequencies in the middle of the image
    #Divide the each FFT bandwidth (5 kHz per channel) into 5 output bands, one per column
    #Currently they're just divided evenly, but in the future the width of each output band will be
    #tuned to have the most movement on the LED matrix
    column_bw = len(fft_L) // 5 #len(fft_L) == len(fft_R)
    column


    for y in range(10):
        for x in range(5): 
            #Average the magnitudes of the frequencies in each output band
            band_mag_L = np.mean( [ abs(fft_L[x*column_bw+w]) for w in range(column_bw) ] )
            band_mag_R = np.mean( [ abs(fft_R[x*column_bw+w]) for w in range(column_bw) ] )
            if(x == 0):
                #lowest frequencies always seem to have MUCH higher magnitude than the rest, this just makes it look nicer
                #Will be tuned in the future
                band_mag_L -= 10000
                band_mag_R -= 10000

            #This normalization value will need to be tuned as well
            mag_normalized_L = band_mag_L / 500 # normalize to value between 0 and 10 to compare against row height 
            mag_normalized_R = band_mag_R / 500
            #turn on neopixels in each respective column
            if(mag_normalized_L < y)
                image[4 - x][y] = ColorPicker(y, 1)
            if(mag_normalized_R < y)
                image[5 + x][y] = ColorPicker(y, 0)


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

num_samples = 1500 #Number of samples taken per loop, needs to be tuned and hopefully multiprocessing helps

pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.2, auto_write = False, pixel_order=ORDER)

image = [[(0, 0, 0) for x in range(10)] for y in range(10)]


try:
    while True:
        if(isStereo):
            StereoSpectrumVisualizer()
        else: #MONO AUX or MIC Input
            MonoSpectrumVisualizer()

except KeyboardInterrupt:
    pixels.deinit()
    wiringpi.digitalWrite(E_pin, 1) #disable MUX output
    sys.exit()
