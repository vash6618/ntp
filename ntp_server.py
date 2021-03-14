import socket
import pickle
import struct
import datetime
import time

NTP_DELTA = (datetime.date(*time.gmtime(0)[0:3]) - datetime.date(1900, 1, 1)).days * 24 * 60 * 60

def _to_time(integ, frac, n=32):
    return integ + float(frac) / 2 ** n


def system_to_ntp_time(timestamp):
    return timestamp + NTP_DELTA

class NTPPacket:
    _PACKET_FORMAT = "!B B b b 3I 4d"

    def __init__(self, mode=3, xmt_timestamp=0):
        self.li = 0

        self.version = 4

        self.mode = mode

        self.stratum = 0

        self.poll = 0

        self.precision = 0

        self.root_delay = 0

        self.root_dispersion = 0

        self.reference_id = 0

        self.reference_timestamp = 0

        self.org_timestamp = 0

        self.rcv_timestamp = 0

        self.xmt_timestamp = xmt_timestamp

    def convert_to_bytes(self):

        byte_string = struct.pack(NTPPacket._PACKET_FORMAT,
                                  (self.li << 6 | self.version << 3 | self.mode),
                                  self.stratum,
                                  self.poll,
                                  self.precision,
                                  self.root_delay,
                                  self.root_dispersion,
                                  self.reference_id,
                                  self.reference_timestamp,
                                  self.org_timestamp,
                                  self.rcv_timestamp,
                                  self.xmt_timestamp)
        return byte_string

    def convert_to_obj(self, data):
        unpacked = struct.unpack(NTPPacket._PACKET_FORMAT,
                                 data[0:struct.calcsize(NTPPacket._PACKET_FORMAT)])
        # except struct.error:
        #     raise NTPException("Invalid NTP packet.")
        # 111.110

        self.li = unpacked[0] >> 6 & 0x3
        self.version = unpacked[0] >> 3 & 0x7
        self.mode = unpacked[0] & 0x7
        self.stratum = unpacked[1]
        self.poll = unpacked[2]
        self.precision = unpacked[3]
        self.root_delay = unpacked[4]
        self.root_dispersion = unpacked[5]
        self.reference_id = unpacked[6]
        self.reference_timestamp = unpacked[7]
        self.org_timestamp = unpacked[8]
        self.rcv_timestamp = unpacked[9]
        self.xmt_timestamp = unpacked[10]


def print_time(t):
    print(t, "{0:.16f}".format(t))

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))

while True:
    data, addr = sock.recvfrom(1024)
    rcv_timestamp = system_to_ntp_time(time.time())


    packet = NTPPacket()
    packet.convert_to_obj(data)
    packet.mode = 4
    packet.org_timestamp = packet.xmt_timestamp
    packet.rcv_timestamp = rcv_timestamp
    packet.xmt_timestamp = system_to_ntp_time(time.time())

    print_time(packet.org_timestamp)
    print_time(packet.rcv_timestamp)
    print_time(packet.xmt_timestamp)
    print("----------------------------------------")
    message = packet.convert_to_bytes()
    sock.sendto(message, addr)
    # print("received message: %s" % data)



