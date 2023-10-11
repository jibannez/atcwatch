#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Authors:
# Jorge Ibáñez Gijón <jorge.ibannez@uam.es> [2022-]
# Departamento de Psicología Básica, Facultad de Psicología
# Universidad Autónoma de Madrid
#
# © Copyright 2022 Jorge Ibáñez Gijón. All rights reserved

# Primitive TCP server to handle conflict severity messages
import time
try:
    import usocket as socket
except:
    import socket
    
from fonts import notosans_32 as font

from . import config

WHITE = const(0xFFFF)
BLACK = const(0x0000)

def color565(r=0, g=0, b=0):
    """Convert red, green and blue values (0-255) into a 16-bit 565 encoding.  As
    a convenience this is also available in the parent adafruit_rgb_display
    package namespace."""
    return (r & 0xf8) << 8 | (g & 0xfc) << 3 | b >> 3
    
    
def tcplistener(twatch, mode=1):
    ########################################        
    # Select configuration
    ########################################        
    if mode == 1:
        config.DEBUG_PRINT = False
        config.SHOW_COLOR = False
        config.SHOW_TEXT = False
        config.WAIT_FOR_TOUCH = False
        config.NOTIFICATION_TIME = 4
    elif mode == 2:
        config.DEBUG_PRINT = False
        config.SHOW_COLOR = False
        config.SHOW_TEXT = True
        config.WAIT_FOR_TOUCH = False
        config.NOTIFICATION_TIME = 4
        
    ########################################            
    # Create server listening on TCP socket
    ########################################            
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((config.HOST, config.PORT))
    s.listen(1)
    time.sleep(2)
    
    ########################################        
    # Turn off screen and wait for messages in an infinite loop
    ########################################        
    twatch.bl.value(0)
    while True:
        # Enclose all loop in a try statement because we do not want it
        # to fail under no circumstance. Exceptions are simply signaled so,
        # if they start to appear, the hardware must be debugged.
        try:
            #Accept connection from client with new severity message
            conn, addr = s.accept()
            request = conn.recv(1024)
            conn.send(b'ACK')
            conn.close()
            
            # Parse message, in a try block to avoid any issues with malformed input
            # Any remaining exceptions are printed out because they indicate a harware issue
            try:
                severity = request[0] 
                aircrafts = request[1:].decode()
                if '-' in aircrafts:
                    aircraftlist = aircrafts.split('-')
                elif '_' in aircrafts:
                    aircraftlist = aircrafts.split('_')
                else:
                    # If the message does not conform to the expected format, 
                    # the default behavior is to print it verbatim.
                    # Fixes a bug discovered using malformed messages for testing.
                    aircraftlist = []
            except:
                # Next loop, because the message could not be parsed
                continue
                
            
            # Scale severity in 0-255 interval
            scaled = 8*severity-1
            
            # Show feedback
            if config.DEBUG_PRINT:
                print('Got a connection from %s' % str(addr))
                print('Severity = %d' % severity)        
                print('Aircrafts = %s' % aircrafts)        
                print("New severity=%d; Scaled=%d" % (severity,scaled))
                
            ########################################        
            # Deal with message according to config
            ########################################        
            if config.SHOW_COLOR:
                color = color565(scaled, g=0, b=255-scaled)
                twatch.disp.fill(color)
                twatch.bl.value(config.BACKLIGHTLEVEL)
                
            if config.SHOW_TEXT:
                if config.SHOW_COLOR == False:
                    twatch.disp.fill(BLACK)
                    twatch.bl.value(config.BACKLIGHTLEVEL)
                    color = BLACK
                    
                if len(aircraftlist) == 2:
                    # The message contained the names of two aircrafts in conflict
                    twatch.disp.write(font, aircraftlist[0], 40, 80, fg=WHITE, bg=color)
                    twatch.disp.write(font, aircraftlist[1], 40, 140, fg=WHITE, bg=color)
                else:
                    # Most likely the message is part of a test
                    twatch.disp.write(font, aircrafts, 1, 100, fg=WHITE, bg=color)            
                
            ########################################
            # Regardless of configuration it must always vibrate
            ########################################
            twatch.buzz.vibrate(1, severity)
            
            ########################################        
            # Notification must appear at least 
            # NOTIFICATION_TIME seconds        
            ########################################        
            time.sleep(config.NOTIFICATION_TIME)
            
            ########################################        
            # Wait for touch event if configured to
            ########################################        
            if config.WAIT_FOR_TOUCH:
                twatch.touched = False # reset state
                while twatch.touched == False:
                    time.sleep(1)
                twatch.touched = False # Reset the touched state        
            
            ########################################        
            # Turn off vibration
            ########################################                
            twatch.buzz.off() # Turn off buzzer
    
            ########################################                            
            # Switch color and turn off screen if configured
            ########################################        
            if config.SHOW_COLOR or config.SHOW_TEXT:        
                twatch.disp.fill(config.BGCOLOR)
                time.sleep(2) # Show the green screen for a while before turning off
                twatch.bl.value(0) # Turn off screen backlight
        except:
            print('There was an exception on tcplistener, not dealing with it')
    
    
def client(msg=config.TEST_MESG, host='192.168.4.1', port=config.PORT):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.send(msg)
    print(s.recv(1024).decode())
    s.close()
