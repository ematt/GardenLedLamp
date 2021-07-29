import struct
import argparse
import signal
import sys
import logging
from tkinter.tix import Tree
from typing import List, Dict, Optional

import cmd2
from cmd2 import (
    bg,
    fg,
    style,
)

from sp import *
from utils import *
from LedColor import *
from Animation import *
from TransportLayer import *
from LampDevice import *


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
            startup_script='cmd_scripts/startup.txt',
            include_ipy=True,
        )

        self.intro = style(
            'Welcome to PyOhio 2019 and cmd2!', bold=True) + ' 😀'

        # Allow access to your application in py and ipy via self
        self.self_in_py = True

        self.debug = True

        # Set the default category name
        self.default_category = 'cmd2 Built-in Commands'

        port = TransportLayer()
        self.poutput("Connected to {}".format(port.getName()))
        self.bus = SPBus(port)
        self.bus.start()

        # Make maxrepeats settable at runtime
        self.broadcastDevice = BroadcastLampDevice(self.bus)
        self.devices = []
        self.selectedDevice = self.broadcastDevice
        self.selectedDeviceId = self.selectedDevice.getBusId()

        self.animationWorker = None

        self.add_settable(cmd2.Settable('selectedDeviceId', int,
                          'Selected device by ID', self, choices_provider=self.select_device_provider, onchange_cb=self.onchange_select_device))

        logging.basicConfig(level=logging.ERROR)

    def cleanup(self):
        if self.animationWorker is not None:
            self.animationWorker.stop()
        self.bus.stop()

    def select_device_provider(self, u) -> List[str]:
        ids = [device.getBusId() for device in self.devices]
        return [str(id) for id in ids] + [str(self.broadcastDevice.getBusId())]

    def onchange_select_device(self, param_name, old, new):
        if new == self.broadcastDevice.getBusId():
            self.selectedDevice = self.broadcastDevice
            return

        for device in self.devices:
            if device.getBusId() == new:
                self.selectedDevice = device
                return

        self.selectedDeviceId = old
        self.poutput("Failed to set device")

    def do_quit(self, _: argparse.Namespace) -> Optional[bool]:
        self.onecmd("set selectedDeviceId 254")
        self.onecmd("set_color -c black")

        self.cleanup()

        return super().do_quit(_)

    @cmd2.with_category(PC)
    def do_serial_clean(self, arg):
        """Reset communication port"""
        self.bus.reset()

    sleep_parser = cmd2.Cmd2ArgumentParser(
        description='Delay execution for x ms')
    sleep_parser.add_argument(
        '-d', '--duration', type=int, help="Delay duration", required=True)
    @cmd2.with_category(PC)
    @cmd2.with_argparser(sleep_parser)
    def do_sleep(self, args):
        duration = args.duration
        self.poutput("Sleeping for {} ms".format(duration))
        time.sleep(duration/1000)

    power_parser = cmd2.Cmd2ArgumentParser(
        description='Enable or disable led strip')
    power_parser.add_argument(
        '-a', '--action', choices=['set', 'get'], help="Action to execute")
    power_parser.add_argument(
        '-v', '--value', choices=['on', 'off'], help='value to set')

    @cmd2.with_category(LED_LAMP)
    @cmd2.with_argparser(power_parser)
    def do_power(self, args: argparse.Namespace):
        """Led strip power"""

        if args.action == 'set':
            reply = self.selectedDevice.sendRequest(SPMessage.COMMAND.SET_POWER, c_ubyte(
                0x00) if args.value == 'off' else c_ubyte(0x01))
        else:
            reply = self.selectedDevice.sendRequest(
                SPMessage.COMMAND.GET_POWER, None)

        self.poutput(reply)

    strip_parser = cmd2.Cmd2ArgumentParser(description='Manage strip len')
    strip_parser.add_argument(
        '-a', '--action', choices=['get'], help="Action to execute")

    @cmd2.with_category(LED_LAMP)
    @cmd2.with_argparser(strip_parser)
    def do_strip_len(self, args: argparse.Namespace):
        reply = self.selectedDevice.sendRequest(
            SPMessage.COMMAND.GET_STRIP_LEN, None)
        self.poutput(reply)

    strip_intensity_parser = cmd2.Cmd2ArgumentParser(
        description='Manage strip intensity')
    strip_intensity_parser.add_argument(
        '-a', '--action', choices=['get', 'set'], help="Action to execute")
    strip_intensity_parser.add_argument(
        '-v', '--value', type=int, choices=range(0, 256), help='Intensity to set')

    @cmd2.with_category(LED_LAMP)
    @cmd2.with_argparser(strip_intensity_parser)
    def do_intensity(self, args: argparse.Namespace):
        if args.action == 'set':
            reply = self.selectedDevice.sendRequest(
                SPMessage.COMMAND.SET_LUMINOSITY, c_ubyte(args.value))
        else:
            reply = self.selectedDevice.sendRequest(
                SPMessage.COMMAND.GET_LUMINOSITY, None)

        self.poutput(reply)

    strip_ct_parser = cmd2.Cmd2ArgumentParser(
        description='Manage strip color temperature')
    strip_ct_parser.add_argument(
        '-a', '--action', choices=['get', 'set'], help="Action to execute")
    strip_ct_parser.add_argument(
        '-v', '--value', type=int, help='Color temperature to set')
    strip_ct_parser.add_argument(
        '-t', '--temperature', type=int, help='Color temperature to set')

    @cmd2.with_category(LED_LAMP)
    @cmd2.with_argparser(strip_ct_parser)
    def do_color_temperature(self, args: argparse.Namespace):
        if args.action == 'set':
            if args.temperature:
                color = LedColor.fromTemperature(args.temperature)
                colorInt = int(color)
            else:
                colorInt = args.value

            reply = self.selectedDevice.sendRequest(
                SPMessage.COMMAND.SET_COLOR_TEMPERATURE, c_uint(colorInt))
        else:
            reply = self.selectedDevice.sendRequest(
                SPMessage.COMMAND.GET_COLOR_TEMPERATURE, None)

        self.poutput(reply)

    strip_cc_parser = cmd2.Cmd2ArgumentParser(
        description='Manage strip color correction')
    strip_cc_parser.add_argument(
        '-a', '--action', choices=['get', 'set'], help="Action to execute")
    strip_cc_parser.add_argument(
        '-v', '--value', type=int, help='Color correction to set')

    @cmd2.with_category(LED_LAMP)
    @cmd2.with_argparser(strip_cc_parser)
    def do_color_correction(self, args: argparse.Namespace):
        if args.action == 'set':
            reply = self.selectedDevice.sendRequest(
                SPMessage.COMMAND.SET_COLOR_CORRECTION, c_uint(args.value))
        else:
            reply = self.selectedDevice.sendRequest(
                SPMessage.COMMAND.GET_COLOR_CORRECTION, None)

    device_model_parser = cmd2.Cmd2ArgumentParser(
        description='Reads device model')

    @cmd2.with_category(LED_LAMP)
    @cmd2.with_argparser(device_model_parser)
    def do_device_model(self, args: argparse.Namespace):
        reply = self.selectedDevice.sendRequest(
            SPMessage.COMMAND.GET_MODEL, None)

        self.poutput("Model: {}".format(reply.payload))

    device_uuid_parser = cmd2.Cmd2ArgumentParser(
        description='Reads device UUID')

    @cmd2.with_category(LED_LAMP)
    @cmd2.with_argparser(device_uuid_parser)
    def do_device_uuid(self, args: argparse.Namespace):
        reply = self.selectedDevice.sendRequest(
            SPMessage.COMMAND.GET_UUID, None)

        self.poutput("UUID: {}".format(reply.payload.hex()))

    device_fw_version_parser = cmd2.Cmd2ArgumentParser(
        description='Reads device FW version')

    @cmd2.with_category(LED_LAMP)
    @cmd2.with_argparser(device_fw_version_parser)
    def do_device_fw_version(self, args: argparse.Namespace):
        reply = self.selectedDevice.sendRequest(
            SPMessage.COMMAND.GET_VERSION, None)

        self.poutput("Fw version: {}".format(reply.payload))

    set_color_parser = cmd2.Cmd2ArgumentParser(
        description='Set led strip color')
    set_color_parser.add_argument('-c', '--color', help="Color name to set")
    set_color_parser.add_argument('-rgb', nargs=3, help="RGB color to set")

    @cmd2.with_category(LED_LAMP)
    @cmd2.with_argparser(set_color_parser)
    def do_set_color(self, args: argparse.Namespace):
        color_rgb = LedColor.fromColorName('white')

        if args.color:
            color_rgb = LedColor.fromColorName(args.color)

        elif args.rgb:
            color_rgb = LedColor(args.rgb[0], args.rgb[1], args.rgb[2])

        self.poutput("Setting color to {}".format(color_rgb))

        color_raw = struct.pack(">BBB", color_rgb.r, color_rgb.g, color_rgb.b)

        reply = self.selectedDevice.sendRequest(
            SPMessage.COMMAND.UPDATE_LED_COLOR, color_raw)

        self.poutput(reply)

    @cmd2.with_category(LED_LAMP_ANIMATION)
    def do_animate_rainbow_full(self, args: argparse.Namespace):
        while True:
            for i in range(0, 255, 1):
                color = colorwheel(i)
                self.onecmd(
                    "set_color -rgb {} {} {}".format(color.r, color.g, color.b))

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

        defaultTimeout = self.bus.getTimeout()
        self.bus.setTimeout(0.05)

        self.devices = []
        for address in range(firstAddress, lastAddress):
            self.poutput("Scanning {}".format(address))
            msg = SPMessageBuilder.buildSp(
                address, SPMessage.COMMAND.PING, None)
            reply = self.bus.sendMessageAndWaitReply(msg)
            if reply is not False:
                self.poutput("Found device at {}".format(address))
                self.devices.append(LampDevice(self.bus, address))

        self.bus.setTimeout(defaultTimeout)

        for device in self.devices:
            device.init()

            self.poutput("ID {}, Model {}, Fw version {}, UUID {}".format(
                device.getBusId(),
                device.getModel(),
                device.getFwVersion(),
                device.getUUID()
            ))

        self.poutput("{} devices found".format(len(self.devices)))

    animate_parser = cmd2.Cmd2ArgumentParser(
        description='Animation command')
    animate_parser.add_argument(
        '-a', '--action', choices=['stop', 'start'], help="Action to execute")
    animate_parser.add_argument(
        '-s', '--sequence', type=int, choices=range(0, 256), help='Animation sequence')
    animate_parser.add_argument(
        '-d', '--device', type=str, choices=['broadcast', 'all'], help='X')

    @cmd2.with_argparser(animate_parser)
    @cmd2.with_category(LED_LAMP_ANIMATION)
    def do_animate(self, args: argparse.Namespace):


        if args.action == "stop":
            if self.animationWorker is None and not self.animationWorker.isRunning():
                self.poutput("No aimation is running")
                return
            
            self.animationWorker.stop()
            self.poutput("Animation stopped")
            return
        
        if args.action == "start":

            if self.animationWorker is not None and self.animationWorker.isRunning():
                self.animationWorker.stop()
                self.poutput("Current animation has stopped")
        
            if args.device:
                if args.device == "broadcast":
                    devicesToAnimate = [self.broadcastDevice]
                else:
                    devicesToAnimate = self.devices
            
            if self.animationWorker is not None and self.animationWorker.isRunning():
                self.poutput("An animation is alredy running.")
                return

            context = AnimationContext(24)

            animationList = [
                # (SprinkleAnimationTransition, (context, LedColor.fromColorName("red"), LedColor.fromColorName("blue"), 35, 1000)),
                # (FadeAnimation, (context, 1000)),
                # (SprinkleAnimationTransition, (context, LedColor.fromColorName("lime"), LedColor.fromColorName("yellow"), 10, 5000)),
                # (FadeAnimation, (context, 1000, 500)),
                # #(DelayAnimation, (context, 1000)),
                # (SprinkleAnimationTransition, (context, LedColor.fromColorName("blue"), LedColor.fromColorName("lime"), 50, 3000)),
                # (SprinkleAnimationTransition, (context, LedColor.fromColorName("lime"), LedColor.fromColorName("red"), 50, 1000)),
                # (FadeAnimation, (context, 1000)),
                # (SprinkleAnimationTransition, (context, LedColor.fromColorName("yellow"), LedColor.fromColorName("red"), 35, 7000)),
                # (FadeAnimation, (context, 1000)),
                # (SprinkleAnimationTransition, (context, LedColor.fromColorName("yellow"), LedColor.fromColorName("lime"), 35, 7000)),
                # (FadeAnimation, (context, 1000)),
                # (SprinkleAnimationTransition, (context, LedColor.fromColorName("yellow"), LedColor.fromColorName("blue"), 35, 7000)),
                # (FadeAnimation, (context, 1000)),
                (SprinkleAnimationTransition, (context, LedColor.fromColorName(
                    "white"), LedColor.fromColorName("silver"), 10, 1000)),
                (SprinkleAnimation, (context, LedColor.fromColorName(
                    "white"), LedColor.fromColorName("silver"), 35, 5000)),
                
                (FadeAnimation, (context, LedColor.fromColorName("orange"), 1000)),
                (SprinkleAnimationTransition, (context, LedColor.fromColorName(
                    "orange"), LedColor.fromColorName("yellow"), 35, 5000)),
                (SprinkleAnimation, (context, LedColor.fromColorName(
                    "yellow"), LedColor.fromColorName("red"), 10, 5000)),
                (SprinkleAnimationTransition, (context, LedColor.fromColorName(
                    "red"), LedColor.fromColorName("purple"), 35, 5000)),
                (SprinkleAnimationTransition, (context, LedColor.fromColorName(
                    "purple"), LedColor.fromColorName("magenta"), 35, 5000)),
                (SprinkleAnimationTransition, (context, LedColor.fromColorName(
                    "magenta"), LedColor.fromColorName("green"), 10, 5000)),
                (SprinkleAnimationTransition, (context, LedColor.fromColorName(
                    "green"), LedColor.fromColorName("lime"), 20, 5000)),
                (FadeAnimation, (context, LedColor.fromColorName("white"), 1000)),
            ]

            self.animationWorker = AnimationRunner(
                animationList, devicesToAnimate, context)
            self.animationWorker.start()

            self.poutput("Animation started")

from pid import PidFile
def main():
    
    def handle_sigterm(sig, frame):
        app.poutput("SIGTERM received")

        app.onecmd("quit")

        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_sigterm)
    import os
    
    print("PID: {}".format(os.getpid()))

    with PidFile(pidname = '/tmp/led_sp.pid') as pidLock:
        print("Lock by {}".format(pidLock.pidname))

        app = BasicApp()
        app.cmdloop()
        app.cleanup()


if __name__ == '__main__':
    main()
