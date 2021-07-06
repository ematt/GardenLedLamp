import struct
import crcmod
import serial
import argparse
from ctypes import *
from matplotlib import colors
import numpy as np
from enum import IntEnum
from cobs import cobs
import pdb
from random import randrange
from colormath.color_objects import sRGBColor, HSVColor
from colormath.color_conversions import convert_color
from datetime import datetime, timedelta
import time
import webcolors
import collections
import math


class FPS:
    def __init__(self,avarageof=50):
        self.frametimestamps = collections.deque(maxlen=avarageof)
    def __call__(self):
        self.frametimestamps.append(time.time())
        if(len(self.frametimestamps) > 1):
            return len(self.frametimestamps)/(self.frametimestamps[-1]-self.frametimestamps[0])
        else:
            return 0.0


def remap( x, oMin, oMax, nMin, nMax ):

    #range check
    if oMin == oMax:
        return None

    if nMin == nMax:
        return None

    #check reversed input range
    reverseInput = False
    oldMin = min( oMin, oMax )
    oldMax = max( oMin, oMax )
    if not oldMin == oMin:
        reverseInput = True

    #check reversed output range
    reverseOutput = False   
    newMin = min( nMin, nMax )
    newMax = max( nMin, nMax )
    if not newMin == nMin :
        reverseOutput = True

    portion = (x-oldMin)*(newMax-newMin)/(oldMax-oldMin)
    if reverseInput:
        portion = (oldMax-x)*(newMax-newMin)/(oldMax-oldMin)

    result = portion + newMin
    if reverseOutput:
        result = newMax - portion

    return result

"""
    Based on: http://www.tannerhelland.com/4435/convert-temperature-rgb-algorithm-code/
    Comments resceived: https://gist.github.com/petrklus/b1f427accdf7438606a6
    Original pseudo code:
    
    Set Temperature = Temperature \ 100
    
    Calculate Red:
    If Temperature <= 66 Then
        Red = 255
    Else
        Red = Temperature - 60
        Red = 329.698727446 * (Red ^ -0.1332047592)
        If Red < 0 Then Red = 0
        If Red > 255 Then Red = 255
    End If
    
    Calculate Green:
    If Temperature <= 66 Then
        Green = Temperature
        Green = 99.4708025861 * Ln(Green) - 161.1195681661
        If Green < 0 Then Green = 0
        If Green > 255 Then Green = 255
    Else
        Green = Temperature - 60
        Green = 288.1221695283 * (Green ^ -0.0755148492)
        If Green < 0 Then Green = 0
        If Green > 255 Then Green = 255
    End If
    
    Calculate Blue:
    If Temperature >= 66 Then
        Blue = 255
    Else
        If Temperature <= 19 Then
            Blue = 0
        Else
            Blue = Temperature - 10
            Blue = 138.5177312231 * Ln(Blue) - 305.0447927307
            If Blue < 0 Then Blue = 0
            If Blue > 255 Then Blue = 255
        End If
    End If
"""

def convert_K_to_RGB(colour_temperature):
    """
    Converts from K to RGB, algorithm courtesy of 
    http://www.tannerhelland.com/4435/convert-temperature-rgb-algorithm-code/
    """
    #range check
    if colour_temperature < 1000: 
        colour_temperature = 1000
    elif colour_temperature > 40000:
        colour_temperature = 40000
    
    tmp_internal = colour_temperature / 100.0
    
    # red 
    if tmp_internal <= 66:
        red = 255
    else:
        tmp_red = 329.698727446 * math.pow(tmp_internal - 60, -0.1332047592)
        if tmp_red < 0:
            red = 0
        elif tmp_red > 255:
            red = 255
        else:
            red = tmp_red
    
    # green
    if tmp_internal <=66:
        tmp_green = 99.4708025861 * math.log(tmp_internal) - 161.1195681661
        if tmp_green < 0:
            green = 0
        elif tmp_green > 255:
            green = 255
        else:
            green = tmp_green
    else:
        tmp_green = 288.1221695283 * math.pow(tmp_internal - 60, -0.0755148492)
        if tmp_green < 0:
            green = 0
        elif tmp_green > 255:
            green = 255
        else:
            green = tmp_green
    
    # blue
    if tmp_internal >=66:
        blue = 255
    elif tmp_internal <= 19:
        blue = 0
    else:
        tmp_blue = 138.5177312231 * math.log(tmp_internal - 10) - 305.0447927307
        if tmp_blue < 0:
            blue = 0
        elif tmp_blue > 255:
            blue = 255
        else:
            blue = tmp_blue
    
    return red, green, blue

class LedColor:
    
    def __init__(self, r: int, g: int, b: int):
        super().__init__()
        self.r = int(r)
        self.g = int(g)
        self.b = int(b)

    @classmethod
    def fromColorName(cls, color):
        #color_rgb = colors.to_hex(color)
        #return cls(int( color_rgb[1:3], 16 ), int( color_rgb[3:5], 16 ), int( color_rgb[5:7], 16 ))
        color_rgb = webcolors.html5_parse_legacy_color(color)
        return cls(color_rgb.red, color_rgb.green, color_rgb.blue)

    @classmethod
    def fromInt(cls, value: int):
        self.b = value & 255
        self.g = (value >> 8) & 255
        self.r = (value >> 16) & 255

    def __int__(self):
        return (self.r<<16) + (self.g<<8) + self.b

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, LedColor):
            return self.r == other.r and self.g == other.g and self.b == other.b
        return False

    def __repr__(self):
        return "<R:{} G:{} G:{}>".format(self.r, self.g, self.b)


class AnimationContext:
    
    def __init__(self, fps):
        self.fps = fps

    def getFps(self):
        return self.fps


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

    def __init__(self, context: AnimationContext, onColor: LedColor, offColor: LedColor, offCount: int, duration: int):
        super().__init__()

        self.onColor = onColor
        self.offColor = offColor
        self.offCount = min(offCount, 5)
        self.duration = duration
        self.timeLeft = duration

    def computeFrame(self, context: AnimationContext, pixels):

        fpsTime = 1000.0 / context.getFps()
        self.timeLeft -= fpsTime

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
   
        return self.timeLeft <= 0, pixels

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
        
        return False, pixels

    def getLength(self, pixels):
        return Animation.INFINIT_LENGTH


class FadeAnimation(Animation):
    
    def __init__(self, context: AnimationContext, duration, breakAfter=0):
        super().__init__()

        self.duration = duration
        self.timeLeft = self.duration - breakAfter

    def computeFrame(self, context: AnimationContext, pixels):

        if self.timeLeft > 0:
            fpsTime = 1000.0 / context.getFps()
            self.timeLeft -= fpsTime

            noOfFps = self.duration / fpsTime
            fadeStep = 255 / noOfFps

            for i in range(0, len(pixels)):
                pixel = pixels[i]
                adobeRGB = sRGBColor(pixel.r, pixel.g, pixel.b, is_upscaled=True)
                hsv = convert_color(adobeRGB, HSVColor)
                hsv.hsv_v = max(hsv.hsv_v - remap(fadeStep, 0, 255, 0, 1.0), 0)
                adobeRGB = convert_color(hsv, sRGBColor)
                pixel = adobeRGB.get_upscaled_value_tuple()
                pixels[i] = LedColor(pixel[0], pixel[1], pixel[2])

        return self.timeLeft <= 0, pixels

    def getLength(self, pixels):
        return Animation.INFINIT_LENGTH


class DelayAnimation(Animation):
    
    def __init__(self, context: AnimationContext, duration):
        super().__init__()

        self.duration = duration
        self.timeLeft = duration

    def computeFrame(self, context: AnimationContext, pixels):

        fpsTime = 1000.0 / context.getFps()
        self.timeLeft -= fpsTime

        return self.timeLeft <= 0, pixels

    def getLength(self, pixels):
        return Animation.INFINIT_LENGTH


class SPMessage:

    MAGIC = "SP"

    class COMMAND(IntEnum):
        SET_POWER = 0x01
        GET_POWER = SET_POWER | 0x0100

        SET_STRIP_LEN = 0x02
        GET_STRIP_LEN = SET_STRIP_LEN | 0x0100

        SET_LUMINOSITY = 0x03
        GET_LUMINOSITY = SET_LUMINOSITY | 0x0100

        SET_MODEL = 0x04
        GET_MODEL = SET_MODEL | 0x0100

        SET_UUID = 0x05
        GET_UUID = SET_UUID | 0x0100

        SET_COLOR_CORRECTION = 0x06
        GET_COLOR_CORRECTION = SET_COLOR_CORRECTION | 0x0100

        SET_COLOR_TEMPERATURE = 0x07
        GET_COLOR_TEMPERATURE = SET_COLOR_TEMPERATURE | 0x0100

        SET_VERSION = 0x08
        GET_VERSION = SET_VERSION | 0x0100

        UPDATE_LED_COLOR = 0x1000
        UPDATE_LED_PIXELS = UPDATE_LED_COLOR + 1
        UPDATE_LED_PIXELS_WO_ACK = UPDATE_LED_PIXELS + 1

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
        elif(type(self.payload) is c_uint):
            msg += bytearray(struct.pack("<I", self.payload.value))
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
    
    @staticmethod
    def current_milli_time():
        return round(time.time() * 1000)

    def sleepIfNeeded(self, context: AnimationContext, timestamp):
        minDelayValue = 20
        delayBetweenRequests = max(minDelayValue, 1000 / context.getFps())
        delayNow = BasicApp.current_milli_time()
        delDiff = delayNow - timestamp
        if(delDiff <= delayBetweenRequests):
            self.poutput("Sleep for {} ms".format((delayBetweenRequests - delDiff)))

            # startTime = datetime.now()
            # sleepTime = timedelta(milliseconds = (delayBetweenRequests - delDiff))

            # while startTime+sleepTime > datetime.now():
            #     pass
            time.sleep(0.001 * (delayBetweenRequests - delDiff))
            #self.poutput("wake up at {}".format(BasicApp.current_milli_time()))

        return BasicApp.current_milli_time()

    @cmd2.with_category(PC)
    def do_serial(self, arg):
        """Connect to serial"""
        rawData = SPMessageBuilder.buildSp(self.device_id, 1, None)
        self.serialPort.write(rawData)

    @cmd2.with_category(PC)
    def do_serial_clean(self, arg):
        """Connect to serial"""
        self.serialPort.reset_output_buffer()
        self.serialPort.reset_input_buffer()
        
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

    strip_ct_parser = cmd2.Cmd2ArgumentParser(description='Manage strip color temperature')
    strip_ct_parser.add_argument('-a', '--action', choices=['get', 'set'], help="Action to execute")
    strip_ct_parser.add_argument('-v', '--value', type=int, help='Color temperature to set')
    strip_ct_parser.add_argument('-t', '--temperature', type=int, help='Color temperature to set')
    @cmd2.with_category(LED_LAMP)
    @cmd2.with_argparser(strip_ct_parser)
    def do_color_temperature(self, args: argparse.Namespace):
        if args.action == 'set':
            if args.temperature:
                [red, green, blue] = convert_K_to_RGB(args.temperature)
                color = LedColor(red, green, blue)
                colorInt = int(color)
            else:
                colorInt = args.value
            
            msg = SPMessageBuilder.buildSp(self.device_id, SPMessage.COMMAND.SET_COLOR_TEMPERATURE, c_uint(colorInt))
        else:
            msg = SPMessageBuilder.buildSp(self.device_id, SPMessage.COMMAND.GET_COLOR_TEMPERATURE, None)
        
        reply = self.sendMsgAndWaitReply(msg)

    strip_cc_parser = cmd2.Cmd2ArgumentParser(description='Manage strip color correction')
    strip_cc_parser.add_argument('-a', '--action', choices=['get', 'set'], help="Action to execute")
    strip_cc_parser.add_argument('-v', '--value', type=int, help='Color correction to set')

    @cmd2.with_category(LED_LAMP)
    @cmd2.with_argparser(strip_cc_parser)
    def do_color_correction(self, args: argparse.Namespace):
        if args.action == 'set':
            msg = SPMessageBuilder.buildSp(self.device_id, SPMessage.COMMAND.SET_COLOR_CORRECTION, c_uint(args.value))
        else:
            msg = SPMessageBuilder.buildSp(self.device_id, SPMessage.COMMAND.GET_COLOR_CORRECTION, None)
        
        reply = self.sendMsgAndWaitReply(msg)

    set_color_parser = cmd2.Cmd2ArgumentParser(description='Set led strip color')
    set_color_parser.add_argument('-c', '--color', help="Color name to set")
    set_color_parser.add_argument('-rgb', nargs=3, help="RGB color to set")


    device_model_parser = cmd2.Cmd2ArgumentParser(description='Reads device model')
    @cmd2.with_category(LED_LAMP)
    @cmd2.with_argparser(device_model_parser)
    def do_device_model(self, args: argparse.Namespace):
        msg = SPMessageBuilder.buildSp(self.device_id, SPMessage.COMMAND.GET_MODEL, None)
        
        reply = self.sendMsgAndWaitReply(msg)
        self.poutput("Model: {}".format(reply.payload))

    device_uuid_parser = cmd2.Cmd2ArgumentParser(description='Reads device UUID')
    @cmd2.with_category(LED_LAMP)
    @cmd2.with_argparser(device_uuid_parser)
    def do_device_uuid(self, args: argparse.Namespace):
        msg = SPMessageBuilder.buildSp(self.device_id, SPMessage.COMMAND.GET_UUID, None)
        
        reply = self.sendMsgAndWaitReply(msg)

        self.poutput("UUID: {}".format(reply.payload.hex()))

    device_fw_version_parser = cmd2.Cmd2ArgumentParser(description='Reads device FW version')
    @cmd2.with_category(LED_LAMP)
    @cmd2.with_argparser(device_fw_version_parser)
    def do_device_fw_version(self, args: argparse.Namespace):
        msg = SPMessageBuilder.buildSp(self.device_id, SPMessage.COMMAND.GET_VERSION, None)
        
        reply = self.sendMsgAndWaitReply(msg)

        self.poutput("Fw version: {}".format(reply.payload))

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

    @cmd2.with_category(LED_LAMP_ANIMATION)
    def do_animate_intensity(self, args: argparse.Namespace):
        
        self.onecmd("set_color -rgb 255 255 255")

        while True:
            for i in range(0, 255, 1):
                self.onecmd("intensity -a set -v {}".format(i))

            for i in reversed(range(0, 255, 1)):
                self.onecmd("intensity -a set -v {}".format(i))

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
            
        for device in self.devices: 
            msg = SPMessageBuilder.buildSp(device, SPMessage.COMMAND.GET_MODEL, None)
            modelReply = self.sendMsgAndWaitReply(msg)
            msg = SPMessageBuilder.buildSp(device, SPMessage.COMMAND.GET_UUID, None)
            uuidReply = self.sendMsgAndWaitReply(msg)
            msg = SPMessageBuilder.buildSp(device, SPMessage.COMMAND.GET_VERSION, None)
            fwVersionReply = self.sendMsgAndWaitReply(msg)
            self.poutput("ID {}, Model {}, Fw version {}, UUID {}".format(device, modelReply.payload, fwVersionReply.payload, uuidReply.payload.hex()))
            
        self.poutput("{} devices found: {}".format(len(self.devices), self.devices))
    
    @cmd2.with_category(LED_LAMP_ANIMATION)
    def do_animate(self, args: argparse.Namespace):
        
        color_rgb = colors.to_hex('red')
        color_rgb = [int( color_rgb[1:3], 16 ), int( color_rgb[3:5], 16 ), int( color_rgb[5:7], 16 )]

        self.onecmd("intensity -a set -v 128")
        #self.onecmd("color_temperature -a set -t 5000")

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
                        "animationIndex": i,
                        "frame": 0,
                        "fps": FPS(),
                        "timestampLastMsg": 0,
                        "animation": None,
                    })
        else:
            devices.append({
                    "id": self.device_id,
                    "strip": [LedColor(0, 0, 0)]*pixelCount,
                    "transition": True,
                    "animationIndex": 0,
                    "frame": 0,
                    "fps": FPS(),
                    "timestampLastMsg": 0,
                    "animation": None,
                })

        context = AnimationContext(24)

        animationList = [
            (SprinkleAnimationTransition, (context, LedColor.fromColorName("red"), LedColor.fromColorName("blue"), 35, 1000)),
            (FadeAnimation, (context, 1000)),
            (SprinkleAnimationTransition, (context, LedColor.fromColorName("lime"), LedColor.fromColorName("yellow"), 10, 5000)),
            (FadeAnimation, (context, 1000, 500)),
            #(DelayAnimation, (context, 1000)),
            (SprinkleAnimationTransition, (context, LedColor.fromColorName("blue"), LedColor.fromColorName("lime"), 50, 3000)),
            (SprinkleAnimationTransition, (context, LedColor.fromColorName("lime"), LedColor.fromColorName("red"), 50, 1000)),
            (FadeAnimation, (context, 1000)),
            (SprinkleAnimationTransition, (context, LedColor.fromColorName("yellow"), LedColor.fromColorName("red"), 35, 7000)),
            (FadeAnimation, (context, 1000)),
            (SprinkleAnimationTransition, (context, LedColor.fromColorName("yellow"), LedColor.fromColorName("lime"), 35, 7000)),
            (FadeAnimation, (context, 1000)),
            (SprinkleAnimationTransition, (context, LedColor.fromColorName("yellow"), LedColor.fromColorName("blue"), 35, 7000)),
            (FadeAnimation, (context, 1000)),
        ]

        for device in devices:
            device["animation"] = animationList[device["animationIndex"] % len(animationList)][0](*animationList[device["animationIndex"] % len(animationList)][1])

        while True:
            for i in range(0, len(devices)):

                device = devices[i]["id"]
                strip = devices[i]["strip"]

                [animDone, strip] = devices[i]["animation"].computeFrame(context, strip)
                devices[i]["strip"] = strip

                if animDone:
                    devices[i]["animationIndex"] += 1
                    devices[i]["frame"] += 1
                    devices[i]["animation"] = animationList[devices[i]["animationIndex"] % len(animationList)][0](*animationList[devices[i]["animationIndex"] % len(animationList)][1])

                pixels = strip
                pixelData = bytearray()
                for pixel in pixels:
                    pixelData.append(pixel.r)
                    pixelData.append(pixel.g)
                    pixelData.append(pixel.b)

                msgData = struct.pack(">B{}B".format(len(pixelData)), len(pixels), *pixelData)

                msg = SPMessageBuilder.buildSp(device, SPMessage.COMMAND.UPDATE_LED_PIXELS_WO_ACK, msgData) 
                #reply = self.sendMsgAndWaitReply(msg)
                reply = self.sendMsg(msg)

                devices[i]["timestampLastMsg"] = self.sleepIfNeeded(context, devices[i]["timestampLastMsg"])
                self.poutput("Device {}: {} fps".format(devices[i]["id"], devices[i]["fps"]()))

            #if devices[i]["transition"]:
            #    time.sleep(0.5)
            #time.sleep(0.5)

if __name__ == '__main__':
    app = BasicApp()
    app.cmdloop()

