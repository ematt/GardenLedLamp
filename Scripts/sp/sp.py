from TransportLayer import TransportLayer
import struct
from ctypes import *
import crcmod
from enum import IntEnum
from threading import Thread, Event

from numpy.core.shape_base import block
from serial.serialutil import Timeout
from queue import Empty, Queue

class SPMessage:

    MAGIC = "SP"

    class ADDRESS(IntEnum):
        BROADCAST = 254

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

class SPBus:
    def __init__(self, port: TransportLayer) -> None:
        self.port = port
        self.shouldStop = Event()
        self.worker = Thread(target=self.worker)
        self.worker.setDaemon(False)
        self.queue = Queue()

    def worker(self):
        while True:
            try:
                command = self.queue.get(block=True, timeout=1)

                msg = command["msg"]
                dest = command["dest"]
                self.port.sendPackage(msg.serialize())
                if dest is not None:
                    try:
                        data = self.port.readPackage()

                        parseResult = SPMessageBuilder.parseSp(data)
                        if parseResult is not False:
                            dest.put(parseResult)
                    except ValueError:
                        dest.put(False)

                self.queue.task_done()
            except Empty:
                pass 

            if self.shouldStop.is_set():
                break
            

    def start(self):
        self.shouldStop.clear()
        self.worker.start()

    def stop(self):
        if self.shouldStop.is_set():
            return

        self.queue.join()
        self.shouldStop.set()
        self.worker.join()

    def setTimeout(self, timeout):
        self.port.setTimeout(timeout)

    def getTimeout(self):
        return self.port.getTimeout()

    def reset(self):
        self.port.reset()

    def sendMessage(self, msg, replyDestinaton = None):
        self.queue.put(
            {
                "msg": msg,
                "dest": replyDestinaton
            })

    def sendMessageAndWaitReply(self, msg):
        replyQueue = Queue()
        self.sendMessage(msg, replyQueue)
        reply = replyQueue.get()
        return reply

