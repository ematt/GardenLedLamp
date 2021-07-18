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

    def readReply(self):
        try:
            data = self.port.readPackage()

            parseResult = SPMessageBuilder.parseSp(data)
            if parseResult is not False:
                return parseResult
        except ValueError:
            return False

    def sendMsg(self, msg):
        self.bus.sendMessage(msg)

    def sendMsgAndWaitReply(self, msg):
        # self.poutput(msg)
        reply = self.bus.sendMessageAndWaitReply(msg)

        if msg.destId == 254:
            time.sleep(0.01)
            return True

        return reply

    def sendRequest(self, cmd, data):
        msg = SPMessageBuilder.buildSp(self.getBusId(), cmd, data)

        if self.getBusId() == SPMessage.ADDRESS.BROADCAST:
            self.sendMsg(msg)
            return True

        reply = self.bus.sendMessageAndWaitReply(msg)

        return reply

    def sendUTPRequest(self, cmd, data):
        msg = SPMessageBuilder.buildSp(self.getBusId(), cmd, data)

        reply = self.sendMsg(msg)

        return reply

    def sendFrame(self, pixels):
        pixelData = bytearray()
        for pixel in pixels:
            pixelData.append(pixel.r)
            pixelData.append(pixel.g)
            pixelData.append(pixel.b)

        msgData = struct.pack(">B{}B".format(
            len(pixelData)), len(pixels), *pixelData)

        reply = self.sendUTPRequest(
            SPMessage.COMMAND.UPDATE_LED_PIXELS_WO_ACK, msgData)


class BroadcastLampDevice(LampDevice):
    def __init__(self, bus) -> None:
        super().__init__(bus, SPMessage.ADDRESS.BROADCAST.value)
        self.model = "N/A",
        self.fwVersion = "N/A",
        self.uuid = "N/A"
