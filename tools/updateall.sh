#!/bin/bash

cd ../src
for k in axp202c.py bma423.fw bma423.py focaltouch.py\
	 font5x8.bin lily.py pcf8563.py st7789my.py\
         buzzer.py boot.py main.py tcpserver.py config.py; do
  if [ $k -nt .put.ts ] ; then
     echo $k
     ampy -p /dev/ttyACM0 put $k
  fi
done
touch .put.ts
cd ../tools
