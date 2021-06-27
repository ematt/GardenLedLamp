import struct
import crcmod
import serial
import argparse
import time
from ctypes import *
from matplotlib import colors
import numpy as np
from enum import IntEnum
from cobs import cobs
import pdb
from random import randrange
from colormath.color_objects import sRGBColor, HSVColor
from colormath.color_conversions import convert_color

import time
import collections


class FPS:
    def __init__(self,avarageof=50):
        self.frametimestamps = collections.deque(maxlen=avarageof)
    def __call__(self):
        self.frametimestamps.append(time.time())
        if(len(self.frametimestamps) > 1):
            return len(self.frametimestamps)/(self.frametimestamps[-1]-self.frametimestamps[0])
        else:
            return 0.0


class LedColor:
    
    def __init__(self, r, g, b):
        super().__init__()
        self.r = r
        self.g = g
        self.b = b

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, LedColor):
            return self.r == other.r and self.g == other.g and self.b == other.b
        return False

class Animation:

    INFINIT_LENGTH = 0

    def __init__(self):
        pass

    def computeFrame(pixels):
        raise NotImplementedError()

    def getLength(self, pixels):
        raise NotImplementedError()


class Transition(Animation):
    def __init__(self):
        super().__init__()


class SprinkleAnimationTransition(Transition):

    def __init__(self, onColor, offColor, offCount):
        super().__init__()

        self.onColor = onColor
        self.offColor = offColor
        self.offCount = min(offCount, 5)

    def computeFrame(self, pixels):
        for i in range(0, self.offCount):
            pixelsNotSetByIndex = []
            for i in range(0, len(pixels)):
                if pixels[i] != self.onColor and pixels[i] != self.offColor:
                    pixelsNotSetByIndex.append(i)
            try:
                currentLedIndex = pixelsNotSetByIndex[randrange(0, len(pixelsNotSetByIndex))]
            except ValueError:
                currentLedIndex = randrange(0, len(pixels))

            currentLedColor = randrange(0, 2)
            pixels[currentLedIndex] = self.offColor if currentLedColor == 0 else self.onColor
   
        return pixels

    def getLength(self, pixels):
        return len(pixels)/self.offCount

    
class SprinkleAnimation(Animation):
    
    def __init__(self, onColor, offColor, offCount):
        super().__init__()

        self.onColor = onColor
        self.offColor = offColor
        self.offCount = offCount

    def computeFrame(self, pixels):
        for i in range(0, len(pixels)):
            pixels[i] = self.onColor

        for i in range(0, self.offCount):
            currentLedIndex = randrange(0, len(pixels))
            pixels[currentLedIndex] = self.offColor
        
        return pixels

    def getLength(self, pixels):
        return Animation.INFINIT_LENGTH


    
class FadeAnimation(Animation):
    
    def __init__(self, fromColor, toColor, speed):
        super().__init__()

        self.fromColor = fromColor
        self.toColor = toColor
        self.speed = speed

    def computeFrame(self, pixels):
        for i in range(0, len(pixels)):
            pixel = pixels[i]
            adobeRGB = sRGBColor(pixel.r, pixel.g, pixel.b, is_upscaled=True)
            hsv = convert_color(adobeRGB, HSVColor)
            hsv.hsv_v = max(hsv.hsv_v - 0.01, 0)
            adobeRGB = convert_color(hsv, sRGBColor)
            pixel = adobeRGB.get_upscaled_value_tuple()
            pixels[i] = LedColor(pixel[0], pixel[1], pixel[2])
      
        return pixels

    def getLength(self, pixels):
        return Animation.INFINIT_LENGTH


class SPMessage:

    MAGIC = "SP"

    class COMMAND(IntEnum):
        SET_POWER = 0x01
        GET_POWER = SET_POWER | 0x0100
        SET_LUMINOSITY = 0x03
        GET_LUMINOSITY = SET_LUMINOSITY | 0x0100

        SET_STRIP_LEN = 0x02
        GET_STRIP_LEN = SET_STRIP_LEN | 0x0100

        UPDATE_LED_COLOR = 0x1000
        UPDATE_LED_PIXELS = UPDATE_LED_COLOR + 1

        PING = 0xA000

    def __init__(self, destId, cmd, payload, handler):
        self.destId = destId
        self.cmd = int(cmd)
        self.payload = payload
        self.handler = handler

    def serialize(self):
        msg = bytearray(str.encode(SPMessage.MAGIC))
        msg += bytearray(struct.pack("<BHB", self.destId, self.cmd, self.handler))

        if(type(self.payload) is c_ubyte):
            msg += bytearray(struct.pack("<B", self.payload.value))
        elif self.payload is not None:
            msg += bytearray(struct.pack("<{}s".format(len(self.payload)), self.payload))

        crcValue = SPMessageBuilder.computeCrc(msg)
        msg += bytearray(struct.pack("<I", crcValue))
        return msg

    def __repr__(self):
        return str(self.__dict__)


class SPGetPower(SPMessage):
    def __init__(self, deviceId):
        super().__init__(deviceId, 257, None)

def GetSequenceNo():
    GetSequenceNo.counter += 1
    if GetSequenceNo.counter > 255:
        GetSequenceNo.counter = 1
    return GetSequenceNo.counter
GetSequenceNo.counter = 0

class SPMessageBuilder:
    
    @staticmethod
    def computeCrc(data):
        crc32 = crcmod.Crc(0x104C11DB7, initCrc=0, xorOut=0xFFFFFFFF)
        crc32.update(data)

        return crc32.crcValue

    @staticmethod
    def buildSp(id, cmd, data):
        return SPMessage(id, cmd, data, GetSequenceNo())

    @staticmethod
    def parseSp(data):
        try:
            if(data[:2] is not SPMessage.MAGIC):
                pass

            headerSize = struct.calcsize("<xxBHB")
            footerSize = struct.calcsize("<I")
            unpackData = struct.unpack("<xxBHB{}sI".format(len(data) - (headerSize + footerSize)), data)

            msgid = unpackData[0]
            cmd = unpackData[1]
            handler = unpackData[2]
            payload = unpackData[3]
            crc = unpackData[4]

            crcValue = SPMessageBuilder.computeCrc(data[:-footerSize])
            if crc != crcValue:
                return False

            return SPMessage(msgid, cmd, payload, handler)
        except (IndexError, TypeError, struct.error):
            return False


def sendSp(msg):
    cobsEncoded = msg
    print(cobsEncoded)
    print(len(cobsEncoded))


def parseData(cobsEncodedData):
    data = cobsEncodedData
    return SPMessageBuilder.parseSp(data)


# with serial.Serial('COM5', 115200, timeout=1) as ser:
#     data = str.encode("""Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec venenatis, nunc non sollicitudin sollicitudin, elit ante vestibulum nisl, eget fringilla arcu dolor id nisl. Sed sed consequat nulla. Nam ut purus ante. In dolor leo, gravida sit amet commodo a, pretium at nisl. Ut ac congue enim. Phasellus varius urna sed tempor cursus. Donec vehicula suscipit volutpat. Aliquam et fermentum enim. Maecenas porttitor nibh eget interdum consequat.
# Aliquam erat volutpat. Nunc blandit leo id massa lacinia placerat. Phasellus aliquet suscipit odio bibendum viverra. In nec blandit tellus. Proin imperdiet accumsan eros, quis faucibus neque ultrices non. Nullam sodales ultricies felis. Nulla semper nunc quis arcu interdum, et pellentesque risus mattis. Suspendisse imperdiet auctor nisl nec lacinia. Nulla vel arcu sagittis, convallis risus vitae, tristique sem.
# Morbi iaculis suscipit nisl, vel mattis ex euismod vel. Vivamus vel consectetur erat. Proin vel nisl at arcu pellentesque tincidunt ut non at. """)
#     rawData = buildSp(1, 1, data)
#     ser.write(rawData)
#     sendSp(buildSp(1, 2, data))
#     print(parseData(buildSp(1, 2, data)))

#!/usr/bin/env python3
# coding=utf-8
"""A simple example demonstrating the following:
    1) How to add a command
    2) How to add help for that command
    3) Persistent history
    4) How to run an initialization script at startup
    5) How to add custom command aliases using the alias command
    6) Shell-like capabilities
"""
import cmd2
from cmd2 import (
    bg,
    fg,
    style,
)


class BasicApp(cmd2.Cmd):
    LED_LAMP = 'Lampi LED'
    LED_LAMP_ANIMATION = 'Animatii'
    LED_LAMP_NETWORK = 'Network'
    PC = 'PC'

    serialPort = None

    def __init__(self):
        super().__init__(
            multiline_commands=['echo'],
            persistent_history_file='cmd2_history.dat',
            startup_script='scripts/startup.txt',
            include_ipy=True,
        )

        self.intro = style('Welcome to PyOhio 2019 and cmd2!', bold=True) + ' 😀'

        # Allow access to your application in py and ipy via self
        self.self_in_py = True

        self.debug = True

        # Set the default category name
        self.default_category = 'cmd2 Built-in Commands'

        # Make maxrepeats settable at runtime
        self.device_id = 254
        self.add_settable(cmd2.Settable('device_id', int, 'Selected device Id', self, choices=range(1, 110), ))
        self.devices = []

        self.serialPort = serial.Serial('COM8', 460800, timeout=1)
        
        self.poutput("Connected to {}".format(self.serialPort.port))

    def readReply(self):

        data = self.serialPort.read_until(b'\x00')
        #data += b'\x00'
        try:
            bindex = data.index(b'SP')
            if bindex < 1:
                bindex = 1
            #self.poutput(data[bindex-1:-1])
            #self.poutput(data)
            data = cobs.decode(data[bindex-1:-1])

            parseResult = SPMessageBuilder.parseSp(data)
            if parseResult is not False:
                return parseResult
        except ValueError:
            return False

    def sendMsg(self, msg):
        cobsEncoded = cobs.encode(msg.serialize())
        cobsEncoded = bytearray(cobsEncoded)
        cobsEncoded.extend(bytearray('\x00', 'ascii'))
        #print(cobsEncoded)
        self.serialPort.write(cobsEncoded)

    def sendMsgAndWaitReply(self, msg):
        #self.poutput(msg)
        self.sendMsg(msg)
        
        if msg.destId == 254:
            time.sleep(0.01)
            return True

        reply = self.readReply()
        if type(reply) is bool:
            return reply
        
        if reply.handler != msg.handler:
            pdb.set_trace()

        return reply

    @cmd2.with_category(PC)
    def do_serial(self, arg):
        """Connect to serial"""
        rawData = SPMessageBuilder.buildSp(self.device_id, 1, None)
        self.serialPort.write(rawData)
        
    power_parser = cmd2.Cmd2ArgumentParser(description='Enable or disable led strip')
    power_parser.add_argument('-a', '--action', choices=['set', 'get'], help="Action to execute")
    power_parser.add_argument('-v', '--value', choices=['on', 'off'], help='value to set')

    @cmd2.with_category(LED_LAMP)
    @cmd2.with_argparser(power_parser)
    def do_power(self, args: argparse.Namespace):
        """Led strip power"""

        if args.action == 'set':
            msg = SPMessageBuilder.buildSp(self.device_id, SPMessage.COMMAND.SET_POWER, c_ubyte(0x00) if args.value == 'off' else c_ubyte(0x01))
        else:
            msg = SPMessageBuilder.buildSp(self.device_id, SPMessage.COMMAND.GET_POWER, None)
        
        reply = self.sendMsgAndWaitReply(msg)
        self.poutput(reply)
    
    strip_parser = cmd2.Cmd2ArgumentParser(description='Manage strip len')
    strip_parser.add_argument('-a', '--action', choices=['get'], help="Action to execute")

    @cmd2.with_category(LED_LAMP)
    @cmd2.with_argparser(strip_parser)
    def do_strip_len(self, args: argparse.Namespace):
        msg = SPMessageBuilder.buildSp(1, 258, None)
        
        reply = self.sendMsgAndWaitReply(msg)
        self.poutput(reply)

    strip_intensity_parser = cmd2.Cmd2ArgumentParser(description='Manage strip intensity')
    strip_intensity_parser.add_argument('-a', '--action', choices=['get', 'set'], help="Action to execute")
    strip_intensity_parser.add_argument('-v', '--value', type=int, choices=range(0, 256), help='Intensity to set')

    @cmd2.with_category(LED_LAMP)
    @cmd2.with_argparser(strip_intensity_parser)
    def do_intensity(self, args: argparse.Namespace):
        if args.action == 'set':
            msg = SPMessageBuilder.buildSp(self.device_id, SPMessage.COMMAND.SET_LUMINOSITY, c_ubyte(args.value))
        else:
            msg = SPMessageBuilder.buildSp(self.device_id, SPMessage.COMMAND.GET_LUMINOSITY, None)
        
        reply = self.sendMsgAndWaitReply(msg)
        self.poutput(reply)

    set_color_parser = cmd2.Cmd2ArgumentParser(description='Set led strip color')
    set_color_parser.add_argument('-c', '--color', help="Color name to set")
    set_color_parser.add_argument('-rgb', nargs=3, help="RGB color to set")

    @cmd2.with_category(LED_LAMP)
    @cmd2.with_argparser(set_color_parser)
    def do_set_color(self, args: argparse.Namespace):
        color_rgb = colors.to_hex('white')

        if args.color:
            color_rgb = colors.to_hex(args.color)
            color_rgb = [int( color_rgb[1:3], 16 ), int( color_rgb[3:5], 16 ), int( color_rgb[5:7], 16 )]

        elif args.rgb:
            color_rgb = [int( args.rgb[0]), int( args.rgb[1]), int( args.rgb[2])]
            
        self.poutput(color_rgb)

        color_raw = struct.pack(">BBB", color_rgb[0], color_rgb[1], color_rgb[2])

        msg = SPMessageBuilder.buildSp(self.device_id, SPMessage.COMMAND.UPDATE_LED_COLOR, color_raw)
        
        reply = self.sendMsgAndWaitReply(msg)
        self.poutput(reply)

    def colorwheel(self, pos):
        """Colorwheel is built into CircuitPython's _pixelbuf. A separate colorwheel is included
        here for use with CircuitPython builds that do not include _pixelbuf, as with some of the
        SAMD21 builds. To use: input a value 0 to 255 to get a color value.
        The colours are a transition from red to green to blue and back to red."""
        pos = pos % 255
        if pos < 0 or pos > 255:
            return 0, 0, 0
        if pos < 85:
            return int(255 - pos * 3), int(pos * 3), 0
        if pos < 170:
            pos -= 85
            return 0, int(255 - pos * 3), int(pos * 3)
        pos -= 170
        return int(pos * 3), 0, int(255 - (pos * 3))

    # @cmd2.with_category(LED_LAMP_ANIMATION)
    # def do_animate(self, args: argparse.Namespace):
        
    #     t = time.process_time()
    #     #do some stuff

    #     while True:
    #         for i in range(0, 255, 1):
    #             #self.onecmd("intensity -a set -v {}".format(i))
    #             color = self.colorwheel(i)
    #             self.onecmd("set_color -rgb {} {} {}".format(color[0], color[1], color[2]))
                
    #         elapsed_time1 = time.perf_counter() - t

    #         self.poutput("Execution time: {}".format(elapsed_time1))
    #         self.poutput("Time per frame: {}".format(elapsed_time1/len(range(0, 255, 1))))

    # @cmd2.with_category(LED_LAMP_ANIMATION)
    # def do_animate(self, args: argparse.Namespace):
        
    #     ledCount = 35
    #     wheelStart = 0
    #     wheelStep = 5
    #     wheelLedStep = 2
        
    #     intensityChagne = 0
    #     gammaIsOn = True
    #     while True:
    #         wheelStart = wheelStart + wheelStep
    #         if(wheelStart > 255):
    #             wheelStart = 0
    #         ledPixel = bytearray()
    #         for i in range(0, ledCount, 1):
    #             #self.onecmd("intensity -a set -v {}".format(i))
    #             color = self.colorwheel(wheelStart + (wheelLedStep * i))
    #             ledPixel.append(color[0])
    #             ledPixel.append(color[1])
    #             ledPixel.append(color[2])

    #         msgData = struct.pack(">B{}B".format(len(ledPixel)), ledCount, *ledPixel)

    #         msg = SPMessageBuilder.buildSp(self.device_id, SPMessage.COMMAND.UPDATE_LED_PIXELS, msgData)
    #         reply = self.sendMsgAndWaitReply(msg)
    #         self.poutput(reply)

    #         intensityChagne = intensityChagne + 1
    #         if intensityChagne % 255 == 0:
    #             if gammaIsOn:
    #                 self.onecmd("intensity -a set -v 254")
    #                 gammaIsOn = False
    #             else:
    #                 self.onecmd("intensity -a set -v 255")
    #                 gammaIsOn = True
    #         #time.sleep(0.01)

    # @cmd2.with_category(LED_LAMP_ANIMATION)
    # def do_animate(self, args: argparse.Namespace):
        
    #     self.onecmd("set_color -rgb 255 0 0")

    #     while True:
    #         for i in range(0, 255, 1):
    #             self.onecmd("intensity -a set -v {}".format(i))

    #         for i in reversed(range(0, 255, 1)):
    #             self.onecmd("intensity -a set -v {}".format(i))

    @cmd2.with_category(LED_LAMP_NETWORK)
    def do_scan(self, args: argparse.Namespace):
        
        firstAddress = 0b0000
        lastAddress = 0b1111

        defaultTimeout = self.serialPort.timeout
        self.serialPort.timeout = 0.05

        self.devices = []
        for address in range(firstAddress, lastAddress):
            self.poutput("Scanning {}".format(address))
            msg = SPMessageBuilder.buildSp(address, SPMessage.COMMAND.PING, None)
            reply = self.sendMsgAndWaitReply(msg)
            if reply is not False:
                self.poutput("Found device at {}".format(address))
                self.devices.append(address)

        self.serialPort.timeout = defaultTimeout
            
        self.poutput("{} devices found: {}".format(len(self.devices), self.devices))
    
    @cmd2.with_category(LED_LAMP_ANIMATION)
    def do_animate(self, args: argparse.Namespace):
        
        color_rgb = colors.to_hex('red')
        color_rgb = [int( color_rgb[1:3], 16 ), int( color_rgb[3:5], 16 ), int( color_rgb[5:7], 16 )]

        self.onecmd("intensity -a set -v 255")

        devices = self.devices if len(self.devices) > 0 else [self.device_id]
        deviceColors = ['red', 'blue', 'green', 'yellow']
        deviceBgColors = ['blue', 'green', 'yellow', 'red', ]

        pixelCount = 35
        sparkleCount = 35

        devices = []
        if len(self.devices) > 0:
            for i in range(len(self.devices)):
                devices.append({
                        "id": self.devices[i],
                        "strip": [LedColor(0, 0, 0)]*pixelCount,
                        "transition": True,
                        "animationIndex": 0,
                        "frame": 0,
                        "fps": FPS()
                    })
        else:
            devices.append({
                    "id": self.device_id,
                    "strip": [LedColor(0, 0, 0)]*pixelCount,
                    "transition": True,
                    "animationIndex": 0,
                    "frame": 0,
                    "fps": FPS()
                })

        animations = [
            {
            "fg":"red",
            "bg":"blue",
            "sparkleCount":35,
            "frames":100
            },
            {
            "fg":"green",
            "bg":"yellow",
            "sparkleCount":10,
            "frames":200
            },
            {
            "fg":"blue",
            "bg":"green",
            "sparkleCount":50,
            "frames":50
            },
            {
            "fg":"yellow",
            "bg":"red",
            "sparkleCount":35,
            "frames":200
            },
        ]

        while True:
            for i in range(0, len(devices)):

                device = devices[i]["id"]
                strip = devices[i]["strip"]

                color_rgb = colors.to_hex(animations[(i + devices[i]["animationIndex"]) % len(animations)]["fg"])
                color_rgb = LedColor(int( color_rgb[1:3], 16 ), int( color_rgb[3:5], 16 ), int( color_rgb[5:7], 16 ))

                bg_color_rgb = colors.to_hex(animations[(i + devices[i]["animationIndex"]) % len(animations)]["bg"])
                bg_color_rgb = LedColor(int( bg_color_rgb[1:3], 16 ), int( bg_color_rgb[3:5], 16 ), int( bg_color_rgb[5:7], 16 ))

                if(devices[i]["transition"]):
                    animation = SprinkleAnimationTransition(color_rgb, bg_color_rgb, animations[(i + devices[i]["animationIndex"]) % len(animations)]["sparkleCount"])
                else:
                    animation = FadeAnimation(color_rgb, bg_color_rgb, animations[(i + devices[i]["animationIndex"]) % len(animations)]["sparkleCount"])

                strip = animation.computeFrame(strip)
                devices[i]["strip"] = strip

                if(devices[i]["transition"]):
                    if devices[i]["frame"] >= animation.getLength(strip):
                        devices[i]["transition"] = False
                        devices[i]["frame"] = 0
                else:
                    if devices[i]["frame"] >= animations[(i + devices[i]["animationIndex"]) % len(animations)]["frames"]:
                        devices[i]["animationIndex"] = devices[i]["animationIndex"] + 1
                        devices[i]["transition"] = True
                        devices[i]["frame"] = 0
                devices[i]["frame"] = devices[i]["frame"] + 1
                 

                pixels = strip
                pixelData = bytearray()
                for pixel in pixels:
                    pixelData.append(pixel.r)
                    pixelData.append(pixel.g)
                    pixelData.append(pixel.b)

                msgData = struct.pack(">B{}B".format(len(pixelData)), len(pixels), *pixelData)

                msg = SPMessageBuilder.buildSp(device, SPMessage.COMMAND.UPDATE_LED_PIXELS, msgData)
                reply = self.sendMsgAndWaitReply(msg)
                #self.poutput(reply)

                self.poutput("Device {}: {} fps".format(devices[i]["id"], devices[i]["fps"]()))

            #if devices[i]["transition"]:
            #    time.sleep(0.5)
            #time.sleep(0.5)

if __name__ == '__main__':
    app = BasicApp()
    app.cmdloop()

