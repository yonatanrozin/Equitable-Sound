import time, os, socket, network, struct
from machine import I2S, Pin, Timer
from uosc_client import Bundle, Client, create_message


sampleRate = 44100 #sampling rate, in Hz
bitDepth = 16 #sample size, in bits (maybe don't increase this)
recordingLength = 10000 #recording length, in ms

wifi_ssid = 'sandbox370'
wifi_pass = '+s0a+s03!2gether?'

remote_IP = '10.18.83.154' #IP address of target
UDP_port = 8001

#connect to WiFi network
sta_if = network.WLAN(network.STA_IF)
if not sta_if.isconnected():
    sta_if.active(True)
    sta_if.connect(wifi_ssid, wifi_pass)
    while not sta_if.isconnected():
        pass # wait till connection
print("WiFi connected.")

# osc = Client(remote_IP, UDP_port)
mysocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP

bytesPerSample = bitDepth // 8

desiredSamples = recordingLength/1000 * sampleRate
desiredBytes = bytesPerSample * recordingLength/1000 * sampleRate


print(f"Target sample count: {desiredSamples}")


pin_bclk = Pin(0)
pin_lrcl = Pin(1)
pin_dout = Pin(2)

led = Pin("LED", Pin.OUT)

sample_buffer_size = 8000



mic_samples = memoryview(bytearray(sample_buffer_size))


formatString = "<" + str(sample_buffer_size//bytesPerSample) + "h"

def recordingMessage(e):
    try:
        print(f"Recording...\tduration: {int(recorded_time)}ms\tsamples: {readBytesCount//bytesPerSample}")
    except:
        print("oh")

with open("testFile.raw", "wb") as myFile:
    
    audio_in = I2S(0,
               sck=pin_bclk, ws=pin_lrcl, sd=pin_dout,
               mode = I2S.RX,
               bits = bitDepth,
               format = I2S.MONO,
               rate = sampleRate,
               ibuf = sample_buffer_size)
    audio_in.readinto(mic_samples) #read into buffer once to remove starting noise
    
    led.on()
    
    readBytesCount = 0
    startTime = time.ticks_ms()
    recordingMessageTimer = Timer()
    

    try:
        recordingMessageTimer.init(period=1000, callback = recordingMessage)
        
        while readBytesCount < desiredBytes:
#         for i in range(50):
            
            try:
                
                
                # add to total count
                readBytesCount += audio_in.readinto(mic_samples)
                
                I2S.shift(buf=mic_samples, bits=16, shift=3)
                
                #get elapsed time using ms timer
                elapsed_time = (time.ticks_diff(time.ticks_ms(),startTime))
                #get current recording length using sample rate + # of recorded samples
                recorded_time = (readBytesCount/bytesPerSample/sampleRate*1000)
                #get difference in elapsed time from expected
                time_diff = abs(elapsed_time - recorded_time)
                
                if time_diff > 10:
                    raise(RuntimeError("Non-recording processes interfering with recording.")) 
                
#                 format string:
#                 "<" : byte little-endianness
#                 output list size, calculated using input length + size per item
#                 "h" for signed shorts (int16)
               
#                 osc.send('/testing', mic_samples)

                mysocket.sendto(mic_samples, (remote_IP, UDP_port))
            except Exception as e:
                print(e)
                break #stop recording
            
    except Exception as e: #continue to cleanup if error encountered while recording

        print(e)


led.off()
recordingMessageTimer.deinit()
audio_in.deinit()




print(f"Recording done.\tduration: {int(recorded_time)}ms\tsamples: {readBytesCount//bytesPerSample}")