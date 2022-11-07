#!/bin/bash

cd ../src
for k in fonts drivers lily.py\
         buzzer.py boot.py main.py tcpserver.py config.py; do
  echo $k
  ampy -p /dev/ttyACM0 put $k
done
touch .put.ts
cd ../tools
