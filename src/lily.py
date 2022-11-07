#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Authors:
# Jorge Ibáñez Gijón <jorge.ibannez@uam.es> [2022-]
# Departamento de Psicología Básica, Facultad de Psicología
# Universidad Autónoma de Madrid
#
# © Copyright 2022 Jorge Ibáñez Gijón. All rights reserved

import time
from machine import I2C,Pin,reset,SPI
import network
import config

from drivers.st7789py import ST7789, BLACK, WHITE, BLUE, GREEN, RED, CYAN, MAGENTA, YELLOW
from drivers import axp202c as axp202
from drivers import pcf8563
from drivers import focaltouch
if config.ENABLE_BMA:
    from drivers import bma423
import buzzer


# THESE ARE BITMAP BIOS FONTS FOR USE WITH text FUNCTION
#from fonts import vga1_8x16 as font
#from fonts import vga2_bold_16x32 as font
#from fonts import vga1_8x16 as font
from fonts import vga1_8x16 as font

# THESE ARE TFF FONTS FOR USE WITH write FUNCTION
# Fonts larger than 16 pixels require frozing the modules
#from fonts import chango_regular_16 as font
#from fonts import notosans_32 as font



    
def maprange(point,fromrange,torange):
    pnew=int( (float(point)-fromrange[0])*float(torange[1]-torange[0])/float(fromrange[1]-fromrange[0])+torange[0] )
    pnew=min(torange[1],pnew)
    pnew=max(torange[0],pnew)
    return(pnew)
    

class LILY(object):
    def __init__(self):
        self.touched = False
        self.axp=axp=axp202.PMU()
        self.axp.enablePower(axp202.AXP202_LDO2)
        self.axp.enablePower(axp202.AXP202_DCDC3)
        self.axp.clearIRQ()
        # useful shorthands
        self.reset=reset
        self.shutdown=self.axp.shutdown
        self.bl=Pin(15,Pin.OUT) # Was gpio 12 in T-Watch V1
        self.bl.on()
        self.bl.value(config.BACKLIGHTLEVEL)
        self.ir=Pin(13,Pin.OUT)
        self.ir.off()
        if config.USE_PWM_BUZZER:
            self.buzz=buzzer.PWMBuzzer(4)
        else:
            self.buzz=Pin(4,Pin.OUT)
        #self.disp=st7789.ST7789font(None,240,240,reset=None,cs=Pin(5,Pin.OUT),dc=Pin(27,Pin.OUT))
        self.disp=ST7789(None,240,240,reset=None,cs=Pin(5,Pin.OUT),dc=Pin(27,Pin.OUT))                         
        self.i2c0 = axp.bus  # I2C(0,scl.Pin(22), sda=Pin(21))
        self.i2c1 = I2C(1,scl=Pin(32), sda=Pin(23))
        self.disp.init()
        self.disp.rotate(config.ROTATION)
        self.disp.text(font,"booting..",0,0,fg=WHITE, bg=BLACK)
        #self.testimg=self.disp.testimg
        self.hwrtc=pcf8563.PCF8563(self.i2c0)
        self.hwrtc.enable_alarm_interrupt()
        datetime=self.hwrtc.datetime()
        #                      (20, 7, 9, 4, 1, 44, 13)
        yy,mon,dd,dow,hh,mm,ss=datetime
        #self.disp.writestring("%04d-%02d-%02d %02d:%02d:%02d" % (2000+yy,mon,dd,hh,mm,ss) ,0,10)
        self.disp.text(font,"%04d-%02d-%02d %02d:%02d:%02d" % (2000+yy,mon,dd,hh,mm,ss) ,0,40,fg=WHITE, bg=BLACK)
        self.ft=focaltouch.FocalTouch(self.i2c1)
        self._orientation=config.ROTATION # 0 is same as touchscreen. button is on the upper right. 1 rotate ccw, 2 upside down. 3  cw
        self.xrange=[20,220] # position of touch on screen
        self.yrange=[20,220]
        # touch pad interrupt
        if config.ENABLE_BMA:
            self.bma=bma423.BMA423(self.i2c0)
            self.bma.map_int(0,bma423.BMA423_TILT_INT          | bma423.BMA423_WAKEUP_INT | 
                              bma423.BMA423_ANY_NO_MOTION_INT | bma423.BMA423_ACTIVITY_INT | bma423.BMA423_STEP_CNTR_INT )
            self.bma.accel_range=2 #2G
            self.bma.feature_enable('step_cntr')
            self.bma.feature_enable('tilt')
            self.bma.accel_enable=1
            self.bma.step_dedect_enabled=1                   
        else:
            self.bma = None
            
        self.installirqhandler()
        self.init_wifi_ap()
        self.show_startup_message()
        
    def show_startup_message(self):
        self.disp.fill(config.BGCOLOR)
        self.disp.text(font,"Listening to events",10,100,fg=WHITE, bg=BLACK)
        self.disp.text(font,"WIFI IP is " + self.netip,10,140,fg=WHITE, bg=BLACK)
        self.buzz.vibrate(1,30,2)    
            
    def init_wifi_ap(self):
        # Create network hotspot
        self.wifiap = network.WLAN(network.AP_IF)
        #self.wifiap.config(authmode=network.AUTH_WPA2_PSK)
        self.wifiap.config(essid=config.ESSID)
        self.wifiap.config(password=config.PASSWORD)
        self.wifiap.active(True)
        
        print('Connection successful')
        print(self.wifiap.ifconfig())
        self.netip = self.wifiap.ifconfig()[0]
    
        #By default, the IP address is 192.168.4.1
        
    def installirqhandler(self):
        # define the irq handlers within this method so we have
        # access to self (closure) without global variable
        
        self.axp.enableIRQ(axp202.AXP202_PEK_SHORTPRESS_IRQ)
        self.axp.enableIRQ(axp202.AXP202_CHARGING_IRQ)
        self.axp.enableIRQ(axp202.AXP202_CHIP_TEMP_HIGH_IRQ )
        self.axp.enableIRQ(axp202.AXP202_BATT_OVER_TEMP_IRQ )
        self.axp.enableIRQ(axp202.AXP202_CHARGING_FINISHED_IRQ)
        self.axp.enableIRQ(axp202.AXP202_CHARGING_IRQ)
        self.axp.enableIRQ(axp202.AXP202_BATT_EXIT_ACTIVATE_IRQ )
        self.axp.enableIRQ(axp202.AXP202_BATT_ACTIVATE_IRQ )
        
        def tp_interrupt(pin):
            if config.DEBUG_PRINT:
                print("Got Touch Pad Interrupt on pin:",pin)
            self.touched = True

        def axp_interrupt(pin):
            irq=self.axp.readIRQ()
            if config.SHOW_SYSEVENTS_ON_SCREEN:
                self.disp.text("axp interrupt" + hex(irq))
            if config.DEBUG_PRINT:
                print("Got AXP Power Managment Interrupt on pin:",pin," irq=",irq)
            if self.bl.value():
                self.bl.value(0)
            else:
                self.bl.value(config.BACKLIGHTLEVEL)
            self.axp.clearIRQ()

        def rtc_interrupt(pin):
            if config.DEBUG_PRINT:
                print("Got RTC Interrupt on pin:",pin)
                
        if config.ENABLE_BMA:
            def bma_interrupt(pin):
                if config.SHOW_SYSEVENTS_ON_SCREEN:
                    self.disp.text("bma interrupt" + str(pin) ,10,10)
                if config.DEBUG_PRINT:
                    print("Got BMA Accellorator Interrupt on pin:",pin)

        self.tpint=Pin(38,Pin.IN)
        self.tpint.irq(trigger=Pin.IRQ_RISING, handler=tp_interrupt)
        self.rtcint=Pin(37,Pin.IN)
        self.rtcint.irq(trigger=Pin.IRQ_FALLING, handler=rtc_interrupt)
        self.axpint=Pin(35,Pin.IN)
        self.axpint.irq(trigger=Pin.IRQ_FALLING, handler=axp_interrupt)
        
        if config.ENABLE_BMA:
            self.bmaint=Pin(39,Pin.IN)
            self.bmaint.irq(trigger=Pin.IRQ_RISING, handler=bma_interrupt)

    def maptouch(self,touches): # map and rotate touchinput
        mapped=[self.touchmap(touch) for touch in touches]
        return mapped
        
    def touchmap(self,touch):
        x=touch['x']
        y=touch['y']
        id=touch['id']
        x=maprange(x,self.xrange,[0,self.disp.width-1])
        y=maprange(y,self.yrange,[0,self.disp.height-1])
        if self._orientation == 2:
            x=self.disp.width-1-x
            y=self.disp.height-1-y
        elif self._orientation == 1:
            x,y=self.disp.height-y-1 , x
        elif self._orientation == 3:
            x,y = y,self.disp.width-1-x
            
        return{'x':x, 'id':id , 'y':y }
    
    @property
    def orientation(self):
        return self._orientation
        
    @orientation.setter
    def orientation(self,val):
        val=val % 4
        if val < 0:
          val += 4
        self._orientation=val
        self.disp.rotate(val)
            
    def paint(self):
        ft=self.ft
        while True:
            if ft.touched:
                touches=self.maptouch(ft.touches)
                print(touches)
                touch=touches[0]
                self.disp.pixel(touch['x'],touch['y'],st7789.RED)
            else:
                time.sleep_ms(50)
                

# i2c0        
# scan 25 (0x19) bosch BMA423 accellerometer
# scan 53 (0x35) AXP202 power managment?
# scan 81 (0x51) PCF8563 RTC 

#i2c1
# scan 56 (0x38) focaltouch FT6236U


