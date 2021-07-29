from decimal import Clamped
from random import randrange

from LedColor import *
from colormath.color_objects import sRGBColor, HSVColor
from colormath.color_conversions import convert_color
from utils import *
from threading import Thread, Event
import logging

from sp import *

class AnimationContext:
    
    def __init__(self, fps):
        self.fps = fps

    def getFps(self):
        return self.fps


class Animation:

    def __init__(self):
        pass

    def computeFrame(pixels):
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


class SprinkleAnimation(Animation):
    
    def __init__(self, context: AnimationContext, onColor: LedColor, offColor: LedColor, offCount: int, duration: int):
        super().__init__()

        self.onColor = onColor
        self.offColor = offColor
        self.offCount = offCount
        self.duration = duration
        self.timeLeft = duration

    def computeFrame(self, context: AnimationContext, pixels):
        fpsTime = 1000.0 / context.getFps()
        self.timeLeft -= fpsTime

        for i in range(0, len(pixels)):
            pixels[i] = self.onColor

        for i in range(0, self.offCount):
            currentLedIndex = randrange(0, len(pixels))
            pixels[currentLedIndex] = self.offColor
        
        return self.timeLeft <= 0, pixels

class FillAnimation(Animation):
    
    def __init__(self, context: AnimationContext, color: LedColor, duration: int):
        super().__init__()

        self.color = color
        self.duration = duration
        self.timeLeft = duration

    def computeFrame(self, context: AnimationContext, pixels):
        fpsTime = 1000.0 / context.getFps()
        self.timeLeft -= fpsTime

        for i in range(0, len(pixels)):
            pixels[i] = self.color
        
        return self.timeLeft <= 0, pixels


class FadeAnimation(Animation):
    
    def __init__(self, context: AnimationContext, color: LedColor, duration: int, breakAfter=0):
        super().__init__()

        self.duration = duration
        self.color = color
        self.timeLeft = self.duration - breakAfter
        self.firstFrame = True
        self.pixelParams = []

    def computeFrame(self, context: AnimationContext, pixels):

        if self.timeLeft > 0:

            if self.firstFrame:
                self.firstFrame = False
                self.computePixelParams(context, pixels)

            fpsTime = 1000.0 / context.getFps()
            self.timeLeft -= fpsTime

            for i in range(0, len(pixels)):
                pixel = pixels[i]
                hsv = pixel.toHSV()
                hsv.hsv_h += self.pixelParams[i]["h"]    
                hsv.hsv_h = min(max(hsv.hsv_h, 0), 360)
                hsv.hsv_s += self.pixelParams[i]["s"]    
                hsv.hsv_s = min(max(hsv.hsv_s, 0), 1)
                hsv.hsv_v += self.pixelParams[i]["v"]         
                hsv.hsv_v = min(max(hsv.hsv_v, 0), 1)       
                pixels[i] = LedColor.fromHSV(hsv)

        return self.timeLeft <= 0, pixels

    def computePixelParams(self, context: AnimationContext, pixels):

        
        fpsTime = 1000.0 / context.getFps()
        noOfFps = self.duration / fpsTime

        for i in range(0, len(pixels)):
            pixel = pixels[i]

            hsv = pixel.toHSV()
            targetColor = self.color.toHSV()
            
            self.pixelParams.append({
                "h": self.computeParamStep(targetColor.hsv_h, hsv.hsv_h, noOfFps),
                "s": self.computeParamStep(targetColor.hsv_s, hsv.hsv_s, noOfFps),
                "v": self.computeParamStep(targetColor.hsv_v, hsv.hsv_v, noOfFps) 
            })

    def computeParamStep(self, target, current, steps):
        distance = abs(target - current)
        step = distance / steps

        diff = step
        if target < current:
            diff = -1 * diff
        return diff

class DelayAnimation(Animation):
    
    def __init__(self, context: AnimationContext, duration):
        super().__init__()

        self.duration = duration
        self.timeLeft = duration

    def computeFrame(self, context: AnimationContext, pixels):

        fpsTime = 1000.0 / context.getFps()
        self.timeLeft -= fpsTime

        return self.timeLeft <= 0, pixels

class AnimationRunner:
    def __init__(self, animationList, devices, context: AnimationContext) -> None:
        self.animationList = animationList
        self.context = context
        self.devices = []
        self.worker = Thread(target=self.worker)
        self.shouldStop = Event()

        pixelCount = 3+4+4+4+3

        for i in range(len(devices)):
            self.devices.append({
                "device": devices[i],
                "strip": [LedColor(0, 0, 0)]*pixelCount,
                "transition": True,
                "animationIndex": i,
                "frame": 0,
                "fps": FPS(),
                "timestampLastMsg": 0,
                "animation": None,
            })

        for device in self.devices:
            device["animation"] = animationList[device["animationIndex"] % len(animationList)][0](
                *animationList[device["animationIndex"] % len(animationList)][1])

    def start(self):
        self.shouldStop.clear()
        self.worker.start()

    def stop(self):
        self.shouldStop.set()
        self.worker.join()

    def isRunning(self):
        return self.shouldStop.is_set() == False


    def sleepIfNeeded(self, context: AnimationContext, timestamp):
        minDelayValue = 20
        delayBetweenRequests = max(minDelayValue, 1000 / context.getFps())
        delayNow = current_milli_time()
        delDiff = delayNow - timestamp
        if(delDiff <= delayBetweenRequests):
            logging.info("Sleep for {} ms".format(
                (delayBetweenRequests - delDiff)))

            # startTime = datetime.now()
            # sleepTime = timedelta(milliseconds = (delayBetweenRequests - delDiff))

            # while startTime+sleepTime > datetime.now():
            #     pass
            time.sleep(0.001 * (delayBetweenRequests - delDiff))
            #self.poutput("wake up at {}".format(BasicApp.current_milli_time()))

        return current_milli_time()

    def worker(self):

        while True:
            for i in range(0, len(self.devices)):

                if self.shouldStop.is_set():
                    return

                device = self.devices[i]["device"]
                strip = self.devices[i]["strip"]

                [animDone, strip] = self.devices[i]["animation"].computeFrame(
                    self.context, strip)
                self.devices[i]["strip"] = strip

                if animDone:
                    self.devices[i]["animationIndex"] += 1
                    self.devices[i]["frame"] += 1
                    self.devices[i]["animation"] = self.animationList[ self.devices[i]["animationIndex"] % len(
                         self.animationList)][0](* self.animationList[ self.devices[i]["animationIndex"] % len( self.animationList)][1])

                device.sendFrame(strip)

                self.devices[i]["timestampLastMsg"] = self.sleepIfNeeded(
                     self.context,  self.devices[i]["timestampLastMsg"])

                logging.info("Device {}: {} fps".format(
                    device.getBusId(),  self.devices[i]["fps"]()))
