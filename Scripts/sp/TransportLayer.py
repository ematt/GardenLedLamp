import serial
from cobs import cobs


class TransportLayer:

    def __init__(self):
        super().__init__()
        self.serialPort = serial.Serial('COM8', 460800, timeout=1)

    def getName(self):
        return self.serialPort.port

    def readPackage(self):
        data = self.serialPort.read_until(b'\x00')
        #data += b'\x00'
        
        bindex = data.index(b'SP')
        if bindex < 1:
            bindex = 1
        #self.poutput(data[bindex-1:-1])
        #self.poutput(data)
        data = cobs.decode(data[bindex-1:-1])
        return data

    def sendPackage(self, data):
        cobsEncoded = cobs.encode(data)
        cobsEncoded = bytearray(cobsEncoded)
        cobsEncoded.extend(bytearray('\x00', 'ascii'))
        #print(cobsEncoded)
        self.serialPort.write(cobsEncoded)  

    def setTimeout(self, timeout):
        self.serialPort.timeout = timeout

    def getTimeout(self):
        return self.serialPort.timeout

    def reset(self):
        self.serialPort.reset_output_buffer()
        self.serialPort.reset_input_buffer()      
