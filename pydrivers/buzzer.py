#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Authors:
# Jorge Ibáñez Gijón <jorge.ibannez@uam.es> [2022-]
# Departamento de Psicología Básica, Facultad de Psicología
# Universidad Autónoma de Madrid
#
# © Copyright 2022 Jorge Ibáñez Gijón. All rights reserved

import machine
import time

class PWMBuzzer:
    def __init__(self, buzzpin=4):
        self.pp = machine.PWM(machine.Pin(buzzpin))
        self.off()
        
    def buzz(self, freq, t=None):
        if t is not None:     
            self.pp.duty(1)  
            self.pp.freq(freq)
            time.sleep(t)
            self.pp.duty(0)            
        else:
            self.pp.duty(1)
            self.pp.freq(freq)
            
    def vibrate(self, duty, freq, t=None):
        if t is not None: 
            self.pp.duty(duty)
            self.pp.freq(freq)
            time.sleep(t)
            self.off()
        else:
            self.pp.duty(duty)
            self.pp.freq(freq)
        
    def off(self):
        self.pp.duty(0)
        
    def on(self):
        self.pp.duty(100)
        self.pp.freq(100)
