#!/bin/bash

cd led
/home/pi/.cargo/bin/heliocron --latitude 46.78N --longitude 23.47E wait --event sunset && screen -L -Logfile led.log  -d -m /usr/bin/python3 main.py