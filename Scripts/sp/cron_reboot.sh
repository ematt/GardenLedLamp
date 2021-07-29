#!/bin/bash

/home/pi/.cargo/bin/heliocron --latitude 46.78N --longitude 23.47E wait --event sunset

cd led
screen -L -Logfile led.log  -d -m /usr/bin/python3 main.py
