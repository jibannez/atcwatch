#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Authors:
# Jorge Ibáñez Gijón <jorge.ibannez@uam.es> [2022-]
# Departamento de Psicología Básica, Facultad de Psicología
# Universidad Autónoma de Madrid
#
# © Copyright 2022 Jorge Ibáñez Gijón. All rights reserved


import _thread as thread
from drivers.lily import LILY
#from mode import MODE

def main():
    # Initialize Lily manager object
    twatch = LILY()
    # Launch server until killed by keyboard interrupt
    try:
        mode = twatch.select_mode()
        twatch.runloop(mode)
    except KeyboardInterrupt:
        thread.exit()


thread.start_new_thread(main, ())
