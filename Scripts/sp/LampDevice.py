from typing import overload
from sp import *
import time


class LampDevice:

    def __init__(self, bus, busId: int) -> None:
        self.busId = busId
        self.bus = bus
        self.lastMessageTimestamp = 0

    def init(self):
        modelReply = self.sendRequest(SPMessage.COMMAND.GET_MODEL, None)
        uuidReply = self.sendRequest(SPMessage.COMMAND.GET_UUID, None)
        fwVersionReply = self.sendRequest(SPMessage.COMMAND.GET_VERSION, None)

        self.model = modelReply.payload if type(
            modelReply) is not bool else "N/A",
        self.fwVersion = fwVersionReply.payload if type(
            fwVersionReply) is not bool else "N/A",
        self.uuid = uuidReply.payload.hex() if type(uuidReply) is not bool else "N/A"

    def __repr__(self):
        return "<Id:{} Model:{} UUID:{}>".format(self.getBusId(), self.getModel(), self.getUUID())

    def getBusId(self):
        return self.busId

    def getModel(self):
        return self.model

    def getFwVersion(self):
        return self.fwVersion

    def getUUID(self):
        return self.uuid

    def sendMsgAndWaitReply(self, msg):
        return self.bus.sendMessageAndWaitReply(msg)

    def sendRequest(self, cmd, data):
        if self.getBusId() == SPMessage.ADDRESS.BROADCAST:
            return self.sendUTPRequest(cmd, data)

        msg = SPMessageBuilder.buildSp(self.getBusId(), cmd, data)
        reply = self.bus.sendMessageAndWaitReply(msg)

        return reply

    def sendUTPRequest(self, cmd, data):
        msg = SPMessageBuilder.buildSp(self.getBusId(), cmd, data)
        self.bus.sendMessage(msg)

        return True

    def sendFrame(self, pixels):
        pixelData = bytearray()
        for pixel in pixels:
            pixelData.append(pixel.r)
            pixelData.append(pixel.g)
            pixelData.append(pixel.b)

        msgData = struct.pack(">B{}B".format(
            len(pixelData)), len(pixels), *pixelData)

        return self.sendUTPRequest(
            SPMessage.COMMAND.UPDATE_LED_PIXELS_WO_ACK, msgData)

class BroadcastLampDevice(LampDevice):
    def __init__(self, bus) -> None:
        super().__init__(bus, SPMessage.ADDRESS.BROADCAST.value)
        self.model = "N/A",
        self.fwVersion = "N/A",
        self.uuid = "N/A"
    
    def init(self):
        pass

    
