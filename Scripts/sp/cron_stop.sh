#!/bin/bash

/home/pi/.cargo/bin/heliocron --latitude 46.78N --longitude 23.47E wait --event sunrise && kill -SIGTERM $(cat /tmp/led_sp.pid) > kill.log