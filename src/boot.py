#!/usr/bin/python3
# -*- coding: utf-8 -*-

import esp
import gc


# Disable debugging
esp.osdebug(None)

# Enable garbage collection
gc.collect()
